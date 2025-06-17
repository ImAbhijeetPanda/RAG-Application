"""
Performance monitoring utilities for the RAG application
"""

import time
import psutil
import threading
from collections import deque
from datetime import datetime, timedelta


class PerformanceMonitor:
    def __init__(self, max_history=100):
        self.max_history = max_history
        self.query_history = deque(maxlen=max_history)
        self.system_metrics = deque(maxlen=max_history)
        self.start_time = time.time()
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self, interval=30):
        """Start system monitoring in background"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_system, 
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
    
    def _monitor_system(self, interval):
        """Monitor system metrics in background"""
        while self.monitoring:
            try:
                metrics = {
                    'timestamp': time.time(),
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'memory_used_gb': psutil.virtual_memory().used / (1024**3),
                    'disk_usage_percent': psutil.disk_usage('/').percent
                }
                self.system_metrics.append(metrics)
            except Exception:
                pass  # Ignore monitoring errors
            
            time.sleep(interval)
    
    def log_query(self, query_type, duration, success=True, **kwargs):
        """Log a query performance metric"""
        metric = {
            'timestamp': time.time(),
            'query_type': query_type,
            'duration': duration,
            'success': success,
            **kwargs
        }
        self.query_history.append(metric)
    
    def get_performance_summary(self):
        """Get comprehensive performance summary"""
        now = time.time()
        uptime = now - self.start_time
        
        # Query statistics
        recent_queries = [q for q in self.query_history 
                         if now - q['timestamp'] < 3600]  # Last hour
        
        query_stats = self._analyze_queries(recent_queries)
        system_stats = self._analyze_system_metrics()
        
        return {
            'uptime_hours': round(uptime / 3600, 2),
            'total_queries': len(self.query_history),
            'recent_queries_1h': len(recent_queries),
            'query_stats': query_stats,
            'system_stats': system_stats,
            'cache_stats': self._get_cache_stats()
        }
    
    def _analyze_queries(self, queries):
        """Analyze query performance"""
        if not queries:
            return {}
        
        durations = [q['duration'] for q in queries]
        success_rate = sum(1 for q in queries if q['success']) / len(queries)
        
        return {
            'avg_duration': round(sum(durations) / len(durations), 3),
            'min_duration': round(min(durations), 3),
            'max_duration': round(max(durations), 3),
            'success_rate': round(success_rate * 100, 1),
            'queries_per_minute': round(len(queries) / 60, 2)
        }
    
    def _analyze_system_metrics(self):
        """Analyze system performance"""
        if not self.system_metrics:
            return {}
        
        recent_metrics = list(self.system_metrics)[-10:]  # Last 10 readings
        
        if not recent_metrics:
            return {}
        
        return {
            'avg_cpu_percent': round(sum(m['cpu_percent'] for m in recent_metrics) / len(recent_metrics), 1),
            'avg_memory_percent': round(sum(m['memory_percent'] for m in recent_metrics) / len(recent_metrics), 1),
            'current_memory_gb': round(recent_metrics[-1]['memory_used_gb'], 2),
            'disk_usage_percent': round(recent_metrics[-1]['disk_usage_percent'], 1)
        }
    
    def _get_cache_stats(self):
        """Get cache statistics if available"""
        try:
            from src.embeddings import EmbeddingManager
            em = EmbeddingManager()
            return em.get_cache_stats()
        except Exception:
            return {}
    
    def get_alerts(self):
        """Get performance alerts"""
        alerts = []
        
        if self.system_metrics:
            latest = self.system_metrics[-1]
            
            if latest['cpu_percent'] > 80:
                alerts.append({
                    'type': 'warning',
                    'message': f"High CPU usage: {latest['cpu_percent']:.1f}%"
                })
            
            if latest['memory_percent'] > 85:
                alerts.append({
                    'type': 'warning', 
                    'message': f"High memory usage: {latest['memory_percent']:.1f}%"
                })
            
            if latest['disk_usage_percent'] > 90:
                alerts.append({
                    'type': 'error',
                    'message': f"Low disk space: {latest['disk_usage_percent']:.1f}% used"
                })
        
        # Check query performance
        recent_queries = [q for q in self.query_history 
                         if time.time() - q['timestamp'] < 300]  # Last 5 minutes
        
        if recent_queries:
            avg_duration = sum(q['duration'] for q in recent_queries) / len(recent_queries)
            if avg_duration > 10:  # Slow queries
                alerts.append({
                    'type': 'warning',
                    'message': f"Slow query performance: {avg_duration:.1f}s average"
                })
        
        return alerts


# Global performance monitor instance
performance_monitor = PerformanceMonitor()
