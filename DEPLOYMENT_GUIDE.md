# IntelliSearch EC2 Deployment Guide

## 🚀 Quick Start

Your IntelliSearch RAG system is ready for deployment! Follow these steps to get it running on your EC2 instance.

## Prerequisites

✅ **EC2 Instance**: Free tier t2.micro or better  
✅ **SSH Access**: Your .pem key file  
✅ **Security Group**: SSH access configured  
✅ **OpenAI API Key**: (Optional - system can run with Ollama only)

## Step 1: Prepare for Deployment

### Get Your Information Ready

1. **EC2 Public IP**: Find this in your AWS Console → EC2 → Instances
2. **SSH Key Path**: Location of your .pem file (e.g., `~/Downloads/my-key.pem`)
3. **OpenAI API Key**: (Optional) Your API key starting with `sk-`

### Set SSH Key Permissions
```bash
chmod 400 /path/to/your-key.pem
```

## Step 2: Deploy to EC2

### Option A: Secure Deployment (Recommended)
```bash
# Set your API key as environment variable (more secure)
export OPENAI_API_KEY="your-api-key-here"

# Run deployment
./deploy_to_ec2.sh YOUR_EC2_IP /path/to/your-key.pem
```

### Option B: Interactive Deployment
```bash
# Run deployment (will prompt for API key)
./deploy_to_ec2.sh YOUR_EC2_IP /path/to/your-key.pem
```

### Option C: Ollama-Only Deployment (Free)
```bash
# Skip API key prompt (press Enter when asked)
./deploy_to_ec2.sh YOUR_EC2_IP /path/to/your-key.pem
```

## Step 3: Configure Security Group

### AWS Console Method
1. Go to **AWS Console → EC2 → Security Groups**
2. Find your instance's security group
3. Click **"Edit inbound rules"**
4. **Add rule**:
   - Type: `Custom TCP Rule`
   - Port Range: `8501`
   - Source: `0.0.0.0/0`
   - Description: `IntelliSearch web interface`
5. **Save rules**

### AWS CLI Method
```bash
# Get your security group ID
aws ec2 describe-instances --instance-ids YOUR_INSTANCE_ID \
  --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' --output text

# Add the rule (replace sg-xxxxxxxx with your security group ID)
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp \
  --port 8501 \
  --cidr 0.0.0.0/0
```

## Step 4: Start Your Application

### SSH into your instance
```bash
ssh -i /path/to/your-key.pem ubuntu@YOUR_EC2_IP
```

### Start the application
```bash
cd intellisearch
./start_production.sh
```

### Access your application
Open your browser and go to:
```
http://YOUR_EC2_IP:8501
```

## Management Commands

### Service Management
```bash
# Start the service
sudo systemctl start intellisearch

# Stop the service  
sudo systemctl stop intellisearch

# Restart the service
sudo systemctl restart intellisearch

# Check service status
sudo systemctl status intellisearch

# View logs
./start_production.sh logs
```

### Application Management
```bash
# Manual start/stop
./start_production.sh start
./start_production.sh stop
./start_production.sh restart
./start_production.sh status

# View real-time logs
tail -f logs/streamlit.log
```

## Troubleshooting

### Common Issues

#### 1. "This site can't be reached"
**Problem**: Can't access the application  
**Solutions**:
- ✅ Check security group allows port 8501
- ✅ Verify application is running: `sudo systemctl status intellisearch`
- ✅ Check if port is listening: `netstat -tlp | grep 8501`

#### 2. "Connection timeout"
**Problem**: Browser times out  
**Solutions**:
- ✅ Verify EC2 instance is running in AWS Console
- ✅ Check security group configuration
- ✅ Try accessing from different network

#### 3. Application not starting
**Problem**: Service fails to start  
**Solutions**:
- ✅ Check logs: `./start_production.sh logs`
- ✅ Verify dependencies: `pip check`
- ✅ Check disk space: `df -h`
- ✅ Check memory: `free -h`

#### 4. "No search results found"
**Problem**: RAG system not returning results  
**Solutions**:
- ✅ Check if knowledge base is loaded
- ✅ Verify OpenAI API key (if using OpenAI)
- ✅ Test Ollama: `ollama list`
- ✅ Check logs for errors

### Diagnostic Commands

Run these on your EC2 instance to diagnose issues:

```bash
# Check application process
ps aux | grep streamlit

# Check port binding
sudo netstat -tlpn | grep 8501

# Test local connection
curl -I http://localhost:8501

# Check system resources
free -h
df -h

# Check Ollama status
ollama list
curl http://localhost:11434/api/tags

# View application logs
tail -20 logs/streamlit.log
tail -20 logs/service.log
```

## Performance Optimization

### For EC2 Free Tier

Your system is already optimized for free tier, but you can:

1. **Monitor usage**: Check AWS billing dashboard
2. **Set up alerts**: Configure billing alerts
3. **Stop when not needed**: Stop instance to save costs
4. **Use Ollama**: Reduces OpenAI API costs

### Memory Management
```bash
# Check memory usage
free -h

# Clear cache if needed
sync && echo 3 | sudo tee /proc/sys/vm/drop_caches
```

## Advanced Configuration

### Custom Domain (Optional)
1. Register a domain name
2. Use Route 53 for DNS
3. Set up SSL with Let's Encrypt
4. Configure nginx reverse proxy

### Backup Strategy
```bash
# Backup your data
tar -czvf intellisearch-backup.tar.gz \
  /home/ubuntu/intellisearch/storage/ \
  /home/ubuntu/intellisearch/.env

# Restore from backup
tar -xzvf intellisearch-backup.tar.gz
```

### Monitoring Setup
```bash
# Set up log rotation
sudo logrotate -f /etc/logrotate.conf

# Monitor disk usage
du -sh /home/ubuntu/intellisearch/*
```

## Security Best Practices

### 1. Restrict SSH Access
Instead of allowing SSH from anywhere:
```bash
# Get your IP
curl ifconfig.me

# Update security group to use YOUR_IP/32 instead of 0.0.0.0/0
```

### 2. Regular Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Python packages
cd /home/ubuntu/intellisearch
source venv/bin/activate
pip list --outdated
```

### 3. Monitor Access
```bash
# Check who's accessing your app
sudo tail -f /var/log/auth.log
tail -f logs/streamlit.log
```

## Cost Management

### Free Tier Limits
- **EC2**: 750 hours/month (t2.micro)
- **Storage**: 30GB EBS
- **Data Transfer**: 15GB out/month

### Cost Optimization Tips
1. **Stop when not using**: `sudo shutdown -h now`
2. **Use Ollama**: Avoid OpenAI costs
3. **Monitor usage**: AWS billing dashboard
4. **Set billing alerts**: Get notified before charges

### Auto-shutdown (Optional)
```bash
# Edit crontab
crontab -e

# Add line to shutdown at 11 PM (save costs)
0 23 * * * sudo shutdown -h now
```

## Support

### Get Help
1. **Check logs**: Always start with log files
2. **Run validation**: `python validate_ec2_deployment.py`
3. **Review this guide**: Most issues are covered here
4. **AWS Documentation**: For EC2-specific issues

### Useful Resources
- [AWS EC2 Free Tier](https://aws.amazon.com/free/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Ollama Documentation](https://github.com/ollama/ollama)

---

## ✅ Quick Checklist

Before asking for help, verify:

- [ ] EC2 instance is running
- [ ] Security group allows port 8501
- [ ] SSH key has correct permissions (400)
- [ ] Application service is running
- [ ] Logs don't show errors
- [ ] You can SSH into the instance
- [ ] Port 8501 is listening on the instance

---

**🎉 Congratulations! Your IntelliSearch RAG system should now be running successfully on EC2!**