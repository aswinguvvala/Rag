#!/bin/bash
# IntelliSearch Production Startup Script
# Optimized for EC2 Free Tier deployment with auto-recovery

set -e

# Configuration
APP_DIR="/home/ubuntu/intellisearch"
VENV_DIR="$APP_DIR/venv"
LOG_DIR="$APP_DIR/logs"
PID_FILE="$APP_DIR/intellisearch.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Pre-flight checks
pre_flight_checks() {
    log "🔍 Running pre-flight checks..."
    
    # Check if we're in the right directory
    if [ ! -f "$APP_DIR/app.py" ]; then
        error "app.py not found in $APP_DIR"
        exit 1
    fi
    
    # Check virtual environment
    if [ ! -d "$VENV_DIR" ]; then
        error "Virtual environment not found at $VENV_DIR"
        exit 1
    fi
    
    # Check environment file
    if [ ! -f "$APP_DIR/.env" ]; then
        warn "No .env file found - using defaults"
    fi
    
    # Create logs directory
    mkdir -p "$LOG_DIR"
    
    # Check if Ollama is running
    if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        warn "Ollama not responding - will rely on OpenAI"
    else
        success "Ollama is running"
    fi
    
    # Check system resources
    local available_mem=$(free -m | awk 'NR==2{printf "%d", $7}')
    if [ "$available_mem" -lt 200 ]; then
        warn "Low memory available: ${available_mem}MB"
    else
        log "Available memory: ${available_mem}MB"
    fi
    
    success "Pre-flight checks completed"
}

# Stop existing instance
stop_app() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log "🛑 Stopping existing instance (PID: $pid)..."
            kill "$pid"
            sleep 3
            
            # Force kill if still running
            if ps -p "$pid" > /dev/null 2>&1; then
                warn "Force killing stubborn process..."
                kill -9 "$pid"
            fi
        fi
        rm -f "$PID_FILE"
    fi
    
    # Kill any remaining streamlit processes
    pkill -f "streamlit run app.py" 2>/dev/null || true
    success "Previous instances stopped"
}

# Start the application
start_app() {
    cd "$APP_DIR"
    source "$VENV_DIR/bin/activate"
    
    log "🚀 Starting IntelliSearch application..."
    
    # Set environment variables for production
    export PYTHONPATH="$APP_DIR:$PYTHONPATH"
    export STREAMLIT_SERVER_PORT=8501
    export STREAMLIT_SERVER_ADDRESS=0.0.0.0
    export STREAMLIT_SERVER_HEADLESS=true
    export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
    export STREAMLIT_SERVER_FILE_WATCHER_TYPE=none
    export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=50
    
    # Start Streamlit with proper logging
    nohup streamlit run app.py \
        --server.port=8501 \
        --server.address=0.0.0.0 \
        --server.headless=true \
        --browser.gatherUsageStats=false \
        --server.fileWatcherType=none \
        --server.maxUploadSize=50 \
        > "$LOG_DIR/streamlit.log" 2>&1 &
    
    local pid=$!
    echo "$pid" > "$PID_FILE"
    
    # Wait a moment and check if the process started successfully
    sleep 5
    if ps -p "$pid" > /dev/null 2>&1; then
        success "IntelliSearch started successfully (PID: $pid)"
        log "📝 Logs: $LOG_DIR/streamlit.log"
        log "🌐 Access your app at: http://$(curl -s http://checkip.amazonaws.com):8501"
        return 0
    else
        error "Failed to start IntelliSearch"
        if [ -f "$LOG_DIR/streamlit.log" ]; then
            echo "Last 10 lines of log:"
            tail -10 "$LOG_DIR/streamlit.log"
        fi
        return 1
    fi
}

# Health check
health_check() {
    local max_attempts=30
    local attempt=1
    
    log "🔍 Performing health check..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:8501/_stcore/health >/dev/null 2>&1; then
            success "Health check passed"
            return 0
        fi
        
        log "Health check attempt $attempt/$max_attempts..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    error "Health check failed after $max_attempts attempts"
    return 1
}

# Main function
main() {
    echo ""
    echo -e "${GREEN}🌌 IntelliSearch Production Startup${NC}"
    echo "========================================"
    echo ""
    
    # Handle command line arguments
    case "${1:-start}" in
        "start")
            pre_flight_checks
            stop_app
            start_app
            health_check
            ;;
        "stop")
            stop_app
            ;;
        "restart")
            pre_flight_checks
            stop_app
            start_app
            health_check
            ;;
        "status")
            if [ -f "$PID_FILE" ]; then
                local pid=$(cat "$PID_FILE")
                if ps -p "$pid" > /dev/null 2>&1; then
                    success "IntelliSearch is running (PID: $pid)"
                    log "Memory usage: $(ps -p $pid -o rss= | awk '{print int($1/1024)"MB"}')"
                    log "Access URL: http://$(curl -s http://checkip.amazonaws.com):8501"
                else
                    warn "PID file exists but process not running"
                    rm -f "$PID_FILE"
                fi
            else
                warn "IntelliSearch is not running"
            fi
            ;;
        "logs")
            if [ -f "$LOG_DIR/streamlit.log" ]; then
                tail -f "$LOG_DIR/streamlit.log"
            else
                error "No log file found"
            fi
            ;;
        *)
            echo "Usage: $0 {start|stop|restart|status|logs}"
            echo ""
            echo "Commands:"
            echo "  start   - Start the application"
            echo "  stop    - Stop the application"
            echo "  restart - Restart the application"
            echo "  status  - Show application status"
            echo "  logs    - Follow application logs"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"