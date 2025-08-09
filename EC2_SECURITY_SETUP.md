# EC2 Security Group Configuration for IntelliSearch

## Overview
Configure your EC2 security group to allow access to your IntelliSearch application while maintaining security best practices.

## Required Security Group Rules

### Inbound Rules
Add these rules to your EC2 instance's security group:

| Type | Protocol | Port Range | Source | Description |
|------|----------|------------|---------|-------------|
| SSH | TCP | 22 | Your IP/0.0.0.0/0 | SSH access for management |
| Custom TCP | TCP | 8501 | 0.0.0.0/0 | Streamlit application access |
| Custom TCP | TCP | 11434 | 127.0.0.1/32 | Ollama API (localhost only) |

### Outbound Rules
Ensure these outbound rules exist (usually default):

| Type | Protocol | Port Range | Destination | Description |
|------|----------|------------|-------------|-------------|
| All Traffic | All | All | 0.0.0.0/0 | Allow all outbound traffic |

## Step-by-Step Configuration

### Method 1: AWS Console (Recommended)

1. **Navigate to EC2 Dashboard**
   - Go to [AWS EC2 Console](https://console.aws.amazon.com/ec2/)
   - Click on "Instances" in the left sidebar
   - Find your instance and click on it

2. **Access Security Groups**
   - In the instance details, click on the "Security" tab
   - Click on the security group link (e.g., "sg-xxxxxxxxx")

3. **Add Inbound Rules**
   - Click "Edit inbound rules"
   - Click "Add rule" for each required rule:

   **SSH Access (if not already present):**
   - Type: SSH
   - Protocol: TCP
   - Port range: 22
   - Source: My IP (recommended) or 0.0.0.0/0 (less secure)
   - Description: SSH access for management

   **Streamlit Application:**
   - Type: Custom TCP Rule
   - Protocol: TCP
   - Port range: 8501
   - Source: 0.0.0.0/0
   - Description: IntelliSearch web interface

4. **Save Rules**
   - Click "Save rules"
   - Wait for the changes to propagate (usually immediate)

### Method 2: AWS CLI

If you prefer command line, use these commands:

```bash
# Get your security group ID
aws ec2 describe-instances --instance-ids YOUR_INSTANCE_ID \
  --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' --output text

# Add Streamlit rule (replace sg-xxxxxxxx with your security group ID)
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp \
  --port 8501 \
  --cidr 0.0.0.0/0

# Verify the rules
aws ec2 describe-security-groups --group-ids sg-xxxxxxxx
```

## Security Best Practices

### 1. Restrict SSH Access
Instead of allowing SSH from anywhere (0.0.0.0/0), use your specific IP:
- Find your IP: https://whatismyipaddress.com/
- Use `YOUR_IP/32` in the source field

### 2. Consider Using a Reverse Proxy
For production, consider setting up nginx as a reverse proxy:
- Allows HTTPS termination
- Better security headers
- Rate limiting capabilities

### 3. Monitor Access Logs
Enable CloudTrail and VPC Flow Logs to monitor access:
```bash
# Check who's accessing your application
sudo tail -f /home/ubuntu/intellisearch/logs/streamlit.log
```

### 4. Optional: Custom Domain with HTTPS
For a professional setup, consider:
- Registering a domain
- Using Route 53 for DNS
- Setting up SSL certificates with Let's Encrypt

## Testing Your Configuration

### 1. Test SSH Access
```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
```

### 2. Test Application Access
Open in your browser:
```
http://YOUR_EC2_IP:8501
```

### 3. Test from Different Networks
Try accessing from:
- Your home network
- Mobile data
- Different devices

## Troubleshooting

### Common Issues

**"This site can't be reached"**
- Check security group rules
- Verify the application is running: `sudo systemctl status intellisearch`
- Check if port 8501 is listening: `sudo netstat -tlp | grep 8501`

**Connection timeout**
- Verify your EC2 instance is running
- Check if the security group allows inbound traffic on port 8501
- Ensure your application is bound to 0.0.0.0, not localhost

**Application not loading**
- Check application logs: `tail -f /home/ubuntu/intellisearch/logs/streamlit.log`
- Verify dependencies are installed
- Check disk space: `df -h`

### Diagnostic Commands

Run these on your EC2 instance:

```bash
# Check if application is running
ps aux | grep streamlit

# Check port binding
sudo netstat -tlpn | grep 8501

# Check security group from instance
curl -s http://169.254.169.254/latest/meta-data/security-groups

# Test local connectivity
curl -I http://localhost:8501

# Check system resources
free -h
df -h
```

## Cost Optimization

### Free Tier Considerations
- Monitor your usage in AWS Billing Dashboard
- Set up billing alerts
- Consider stopping the instance when not in use
- Use CloudWatch to monitor resource usage

### Automatic Shutdown (Optional)
Create a cron job to shut down during off-hours:
```bash
# Edit crontab
crontab -e

# Add line to shut down at 11 PM daily (save costs)
0 23 * * * sudo shutdown -h now

# Auto-start requires AWS Lambda or other external trigger
```

## Support

If you encounter issues:

1. **Check the troubleshooting section above**
2. **Review application logs**
3. **Verify security group configuration**
4. **Test from multiple networks/devices**

Remember: Changes to security groups take effect immediately, but application changes may require a restart.