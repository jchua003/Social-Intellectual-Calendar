"""
Monitoring System for Museum Scrapers
Tracks success/failure and sends alerts when scrapers break
"""

import json
import os
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class ScraperMonitor:
    def __init__(self):
        self.log_file = 'scraper_logs.json'
        self.config_file = 'monitor_config.json'
        self.load_logs()
        self.load_config()
    
    def load_logs(self):
        """Load existing logs"""
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r') as f:
                self.logs = json.load(f)
        else:
            self.logs = {
                'museums': {},
                'last_successful_run': None,
                'total_events_scraped': 0
            }
    
    def load_config(self):
        """Load monitoring configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                'alert_email': None,
                'failure_threshold': 3,  # Alert after 3 consecutive failures
                'min_events_threshold': 10,  # Alert if total events < 10
                'github_issue': True  # Create GitHub issue on failure
            }
    
    def log_scrape_attempt(self, museum_id, success, events_count=0, error=None):
        """Log a scraping attempt"""
        if museum_id not in self.logs['museums']:
            self.logs['museums'][museum_id] = {
                'last_success': None,
                'last_failure': None,
                'consecutive_failures': 0,
                'total_attempts': 0,
                'success_rate': 0,
                'last_events_count': 0
            }
        
        museum_log = self.logs['museums'][museum_id]
        museum_log['total_attempts'] += 1
        
        if success:
            museum_log['last_success'] = datetime.now().isoformat()
            museum_log['consecutive_failures'] = 0
            museum_log['last_events_count'] = events_count
            self.logs['last_successful_run'] = datetime.now().isoformat()
            self.logs['total_events_scraped'] += events_count
        else:
            museum_log['last_failure'] = datetime.now().isoformat()
            museum_log['consecutive_failures'] += 1
            museum_log['last_error'] = str(error) if error else 'Unknown error'
        
        # Calculate success rate
        successes = museum_log['total_attempts'] - museum_log['consecutive_failures']
        museum_log['success_rate'] = (successes / museum_log['total_attempts']) * 100
        
        self.save_logs()
        
        # Check if we need to send alerts
        self.check_alerts(museum_id)
    
    def check_alerts(self, museum_id):
        """Check if we need to send alerts"""
        museum_log = self.logs['museums'][museum_id]
        
        # Alert if consecutive failures exceed threshold
        if museum_log['consecutive_failures'] >= self.config['failure_threshold']:
            self.send_alert(
                f"Scraper Alert: {museum_id} failing",
                f"The {museum_id} scraper has failed {museum_log['consecutive_failures']} times consecutively.\n"
                f"Last error: {museum_log.get('last_error', 'Unknown')}\n"
                f"Success rate: {museum_log['success_rate']:.1f}%"
            )
        
        # Alert if total events is too low
        if self.logs['total_events_scraped'] < self.config['min_events_threshold']:
            self.send_alert(
                "Low Event Count Alert",
                f"Total events scraped: {self.logs['total_events_scraped']}\n"
                f"This is below the threshold of {self.config['min_events_threshold']}"
            )
    
    def send_alert(self, subject, body):
        """Send alert via configured method"""
        print(f"\n🚨 ALERT: {subject}")
        print(body)
        
        # Create GitHub issue if configured
        if self.config.get('github_issue'):
            self.create_github_issue(subject, body)
        
        # Send email if configured
        if self.config.get('alert_email'):
            self.send_email_alert(subject, body)
    
    def create_github_issue(self, title, body):
        """Create a GitHub issue for the alert"""
        # This would be done via GitHub Actions
        issue_content = f"""
---
title: "{title}"
labels: ["scraper-issue", "automated"]
---

{body}

**Automated Alert Details:**
- Time: {datetime.now().isoformat()}
- Total attempts today: {sum(m['total_attempts'] for m in self.logs['museums'].values())}
- Overall success rate: {self.get_overall_success_rate():.1f}%

**Next Steps:**
1. Check the scraper logs for detailed errors
2. Manually test the failing museum website
3. Update the scraper if the website structure changed
4. Consider switching to CSV import for this museum
"""
        
        # Save to file for GitHub Action to pick up
        with open('alert_issue.md', 'w') as f:
            f.write(issue_content)
    
    def get_overall_success_rate(self):
        """Calculate overall success rate"""
        total_attempts = sum(m['total_attempts'] for m in self.logs['museums'].values())
        total_failures = sum(m['consecutive_failures'] for m in self.logs['museums'].values())
        
        if total_attempts == 0:
            return 0
        
        return ((total_attempts - total_failures) / total_attempts) * 100
    
    def save_logs(self):
        """Save logs to file"""
        with open(self.log_file, 'w') as f:
            json.dump(self.logs, f, indent=2)
    
    def generate_report(self):
        """Generate a status report"""
        report = f"""
# Museum Scraper Status Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overall Statistics
- Total Events Scraped: {self.logs['total_events_scraped']}
- Last Successful Run: {self.logs.get('last_successful_run', 'Never')}
- Overall Success Rate: {self.get_overall_success_rate():.1f}%

## Museum Status
"""
        
        for museum_id, data in self.logs['museums'].items():
            status = "✅" if data['consecutive_failures'] == 0 else "❌"
            report += f"""
### {museum_id.upper()} {status}
- Success Rate: {data['success_rate']:.1f}%
- Last Success: {data.get('last_success', 'Never')}
- Last Event Count: {data.get('last_events_count', 0)}
- Consecutive Failures: {data['consecutive_failures']}
"""
            if data['consecutive_failures'] > 0:
                report += f"- Last Error: {data.get('last_error', 'Unknown')}\n"
        
        return report
    
    def check_scraper_health(self):
        """Check overall scraper health"""
        health_status = {
            'healthy': [],
            'warning': [],
            'critical': []
        }
        
        for museum_id, data in self.logs['museums'].items():
            if data['consecutive_failures'] == 0:
                health_status['healthy'].append(museum_id)
            elif data['consecutive_failures'] < self.config['failure_threshold']:
                health_status['warning'].append(museum_id)
            else:
                health_status['critical'].append(museum_id)
        
        return health_status

# Integration with main scraper
class MonitoredScraper:
    """Wrapper for scrapers with monitoring"""
    
    def __init__(self, scraper_function, museum_id):
        self.scraper = scraper_function
        self.museum_id = museum_id
        self.monitor = ScraperMonitor()
    
    def scrape(self):
        """Run scraper with monitoring"""
        try:
            events = self.scraper()
            success = len(events) > 0
            
            self.monitor.log_scrape_attempt(
                self.museum_id,
                success=success,
                events_count=len(events)
            )
            
            return events
            
        except Exception as e:
            self.monitor.log_scrape_attempt(
                self.museum_id,
                success=False,
                error=e
            )
            raise

# Usage example
if __name__ == "__main__":
    monitor = ScraperMonitor()
    
    # Generate and print report
    print(monitor.generate_report())
    
    # Check health
    health = monitor.check_scraper_health()
    print(f"\nHealthy scrapers: {health['healthy']}")
    print(f"Warning scrapers: {health['warning']}")
    print(f"Critical scrapers: {health['critical']}")
