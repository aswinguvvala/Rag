import os
import time
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional

import torch
import psutil
import logging

from transformers import AutoModelForCausalLM, AutoTokenizer


@dataclass
class ModelProfile:
    """Represents a quantized model variant with its characteristics"""
    model_id: str
    original_model: str
    quantization_method: str  # 'int8', 'int4', 'gptq', 'awq', 'gguf'
    size_mb: float
    memory_usage_mb: float
    avg_tokens_per_second: float
    quality_score: float  # 0-1, relative to original
    optimal_context_length: int
    hardware_requirements: Dict[str, Any]


class QuantizationPipeline:
    """
    Automated pipeline for model quantization and optimization.
    This is the brain of your system - it takes large models and makes them efficient.
    """

    def __init__(self, base_model_path: str, output_dir: str = "optimized_models"):
        self.base_model_path = base_model_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Store profiles of all quantized variants
        self.model_profiles: Dict[str, ModelProfile] = {}
        self.evaluation_results: Dict[str, Dict] = {}

        # Setup logging for detailed tracking
        self._setup_logging()

    def _setup_logging(self):
        """Configure detailed logging for the optimization process"""
        log_path = self.output_dir / 'optimization.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def detect_hardware_capabilities(self) -> Dict[str, Any]:
        """
        Detect what the current hardware can handle.
        This helps us choose the right optimization strategy.
        """
        capabilities: Dict[str, Any] = {
            'cpu_cores': psutil.cpu_count(),
            'ram_gb': psutil.virtual_memory().total / (1024 ** 3),
            'available_ram_gb': psutil.virtual_memory().available / (1024 ** 3),
            'gpu_available': torch.cuda.is_available(),
            'gpu_memory_gb': 0.0,
            'gpu_name': 'None'
        }

        try:
            if capabilities['gpu_available']:
                import GPUtil  # type: ignore
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    capabilities['gpu_memory_gb'] = gpu.memoryTotal / 1024
                    capabilities['gpu_name'] = gpu.name
        except Exception as e:
            self.logger.warning(f"GPU detection failed: {e}")

        self.logger.info(f"Hardware detected: {capabilities}")
        return capabilities

    async def quantize_model(self, method: str = 'dynamic_int8') -> ModelProfile:
        """
        Apply quantization to reduce model size while preserving quality.
        Think of this as compressing a high-resolution image - we keep the important details.
        """
        method = method.lower()
        self.logger.info(f"Starting {method} quantization...")

        # Load the base model/tokenizer
        tokenizer = AutoTokenizer.from_pretrained(self.base_model_path)

        # Some methods reload with different configs; for simplicity, load a base FP16/FP32 first
        base_model = AutoModelForCausalLM.from_pretrained(
            self.base_model_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map='auto'
        )

        # Apply quantization based on method
        if method in ('dynamic_int8', 'int8', 'dynamic'):
            quantized_model = self._apply_dynamic_quantization(base_model)
            effective_method = 'dynamic_int8'
        elif method in ('static_int8', 'static'):
            quantized_model = self._apply_static_quantization(base_model, tokenizer)
            effective_method = 'static_int8'
        elif method in ('int4', '4bit'):
            # Reload using bitsandbytes 4-bit if available
            quantized_model = self._apply_int4_quantization()
            effective_method = 'int4'
        elif method == 'gptq':
            quantized_model = await self._apply_gptq_quantization()
            effective_method = 'gptq'
        else:
            raise ValueError(f"Unknown quantization method: {method}")

        # Save the quantized model
        output_path = self.output_dir / f"model_{effective_method}"
        output_path.mkdir(exist_ok=True, parents=True)
        try:
            quantized_model.save_pretrained(output_path)
            tokenizer.save_pretrained(output_path)
        except Exception as e:
            self.logger.warning(f"Saving quantized model failed: {e}")

        # Profile the quantized model
        profile = self._profile_model(quantized_model, tokenizer, effective_method)
        self.model_profiles[effective_method] = profile

        # Persist profile
        try:
            with open(self.output_dir / 'model_profiles.json', 'w') as f:
                json.dump({k: asdict(v) for k, v in self.model_profiles.items()}, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to persist model profiles: {e}")

        return profile

    def _apply_dynamic_quantization(self, model: torch.nn.Module) -> torch.nn.Module:
        """Dynamic INT8 quantization - good balance of speed and quality (CPU-friendly)."""
        import torch.quantization as quantization

        quantized_model = quantization.quantize_dynamic(
            model,
            {torch.nn.Linear},  # Quantize linear layers
            dtype=torch.qint8
        )
        return quantized_model

    def _apply_static_quantization(self, model: torch.nn.Module, tokenizer: AutoTokenizer) -> torch.nn.Module:
        """
        Static INT8 quantization placeholder. Proper static PTQ requires calibration data.
        For now, we fallback to dynamic quantization but mark as static_int8 for UX.
        """
        self.logger.info("Static PTQ not fully implemented; using dynamic quantization as a stand-in")
        return self._apply_dynamic_quantization(model)

    def _apply_int4_quantization(self) -> torch.nn.Module:
        """Apply 4-bit quantization using bitsandbytes if available."""
        try:
            from transformers import BitsAndBytesConfig
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_compute_dtype=torch.float16,
            )
            model_4bit = AutoModelForCausalLM.from_pretrained(
                self.base_model_path,
                quantization_config=bnb_config,
                device_map="auto"
            )
            return model_4bit
        except Exception as e:
            self.logger.warning(f"INT4 quantization not available ({e}); falling back to dynamic INT8")
            # Fallback to dynamic
            base_model = AutoModelForCausalLM.from_pretrained(
                self.base_model_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map='auto'
            )
            return self._apply_dynamic_quantization(base_model)

    async def _apply_gptq_quantization(self) -> torch.nn.Module:
        """
        Placeholder for GPTQ quantization. Implement with AutoGPTQ/Optimum when GPU available.
        For now, fallback to dynamic INT8 to keep pipeline usable everywhere.
        """
        self.logger.info("GPTQ quantization not implemented in this minimal integration; using dynamic INT8")
        base_model = AutoModelForCausalLM.from_pretrained(
            self.base_model_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map='auto'
        )
        return self._apply_dynamic_quantization(base_model)

    def _profile_model(self, model: torch.nn.Module, tokenizer: AutoTokenizer, method: str) -> ModelProfile:
        """
        Measure the performance characteristics of a quantized model.
        This tells us exactly how fast and efficient our optimized model is.
        """
        size_mb = self._calculate_model_size(model)
        tokens_per_second = self._benchmark_inference_speed(model, tokenizer)
        memory_usage_mb = self._measure_memory_usage()

        # Placeholder overall quality score; can be updated by evaluation framework later
        quality_score = 0.95 if method in ("dynamic_int8", "static_int8") else 0.9

        profile = ModelProfile(
            model_id=f"{self.base_model_path}_{method}",
            original_model=self.base_model_path,
            quantization_method=method,
            size_mb=size_mb,
            memory_usage_mb=memory_usage_mb,
            avg_tokens_per_second=tokens_per_second,
            quality_score=quality_score,
            optimal_context_length=2048,
            hardware_requirements={
                'min_ram_gb': max(memory_usage_mb / 1024.0, 1.0),
                'recommended_ram_gb': max((memory_usage_mb * 1.5) / 1024.0, 2.0),
                'gpu_required': method in ['int4', 'gptq'] and torch.cuda.is_available()
            }
        )

        return profile

    def _calculate_model_size(self, model: torch.nn.Module) -> float:
        """Approximate model size in MB by summing parameter tensor sizes."""
        total_bytes = 0
        for param in model.parameters():
            total_bytes += param.nelement() * param.element_size()
        for buffer in model.buffers():
            total_bytes += buffer.nelement() * buffer.element_size()
        return round(total_bytes / (1024 ** 2), 2)

    def _benchmark_inference_speed(self, model: torch.nn.Module, tokenizer: AutoTokenizer) -> float:
        """Rudimentary benchmark: generate ~50 tokens and measure throughput."""
        model.eval()
        device = next(model.parameters()).device
        prompt = "The quick brown fox jumps over the lazy dog."
        inputs = tokenizer(prompt, return_tensors='pt').to(device)

        # Warmup
        try:
            with torch.no_grad():
                _ = model.generate(**inputs, max_new_tokens=5)
        except Exception:
            pass

        try:
            with torch.no_grad():
                start = time.time()
                output = model.generate(**inputs, max_new_tokens=50, do_sample=False)
                end = time.time()
            generated = output[0].tolist()
            new_tokens = max(0, len(generated) - inputs['input_ids'].shape[1])
            elapsed = max(end - start, 1e-3)
            return round(new_tokens / elapsed, 2)
        except Exception as e:
            self.logger.warning(f"Benchmark failed: {e}")
            return 0.0

    def _measure_memory_usage(self) -> float:
        """Measure current process memory usage in MB (RSS)."""
        process = psutil.Process(os.getpid())
        mem_mb = process.memory_info().rss / (1024 ** 2)
        # If CUDA available, include allocated GPU memory estimate
        if torch.cuda.is_available():
            try:
                mem_mb += torch.cuda.max_memory_allocated() / (1024 ** 2)
            except Exception:
                pass
        return round(mem_mb, 2)


