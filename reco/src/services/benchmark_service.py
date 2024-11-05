import time
import logging
import numpy as np
from typing import Dict, List, Callable
import pandas as pd
from datetime import datetime
import json
from pathlib import Path
import psutil
import GPUtil
from concurrent.futures import ThreadPoolExecutor
import asyncio

logger = logging.getLogger(__name__)

class BenchmarkService:
    def __init__(self, output_dir: str = "metrics/benchmarks"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = {}
        
    def measure_execution_time(
        self,
        func: Callable,
        args: tuple = (),
        kwargs: dict = {},
        n_runs: int = 5
    ) -> Dict:
        """Measure execution time of a function."""
        times = []
        memory_usage = []
        
        for _ in range(n_runs):
            # Record memory before
            memory_before = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            # Time execution
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Record memory after
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_used = memory_after - memory_before
            
            times.append(execution_time)
            memory_usage.append(memory_used)
        
        return {
            'mean_time': np.mean(times),
            'std_time': np.std(times),
            'min_time': min(times),
            'max_time': max(times),
            'mean_memory': np.mean(memory_usage),
            'std_memory': np.std(memory_usage),
            'n_runs': n_runs
        }
        
    async def measure_api_latency(
        self,
        endpoint: str,
        n_requests: int = 100,
        concurrent_requests: int = 10
    ) -> Dict:
        """Measure API endpoint latency."""
        import aiohttp
        
        async def make_request(session, url):
            start_time = time.time()
            async with session.get(url) as response:
                await response.text()
                return time.time() - start_time
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for _ in range(n_requests):
                task = make_request(session, endpoint)
                tasks.append(task)
                
                if len(tasks) >= concurrent_requests:
                    latencies = await asyncio.gather(*tasks)
                    tasks = []
        
        latencies = np.array(latencies)
        return {
            'mean_latency': np.mean(latencies),
            'std_latency': np.std(latencies),
            'p50_latency': np.percentile(latencies, 50),
            'p95_latency': np.percentile(latencies, 95),
            'p99_latency': np.percentile(latencies, 99),
            'n_requests': n_requests
        }
        
    def benchmark_model_inference(
        self,
        model,
        test_data: pd.DataFrame,
        batch_sizes: List[int] = [1, 10, 100]
    ) -> Dict:
        """Benchmark model inference performance."""
        results = {}
        
        for batch_size in batch_sizes:
            batch_times = []
            memory_usage = []
            
            # Split data into batches
            n_batches = len(test_data) // batch_size
            for i in range(n_batches):
                batch = test_data.iloc[i*batch_size:(i+1)*batch_size]
                
                # Measure inference time and memory
                memory_before = psutil.Process().memory_info().rss / 1024 / 1024
                start_time = time.time()
                
                _ = model.predict(batch)
                
                inference_time = time.time() - start_time
                memory_after = psutil.Process().memory_info().rss / 1024 / 1024
                
                batch_times.append(inference_time)
                memory_usage.append(memory_after - memory_before)
            
            results[f'batch_size_{batch_size}'] = {
                'mean_time': np.mean(batch_times),
                'std_time': np.std(batch_times),
                'mean_memory': np.mean(memory_usage),
                'std_memory': np.std(memory_usage),
                'throughput': batch_size / np.mean(batch_times)
            }
            
        return results
        
    def benchmark_database(
        self,
        session,
        queries: Dict[str, str],
        n_runs: int = 5
    ) -> Dict:
        """Benchmark database query performance."""
        results = {}
        
        for query_name, query in queries.items():
            times = []
            
            for _ in range(n_runs):
                start_time = time.time()
                session.execute(query)
                execution_time = time.time() - start_time
                times.append(execution_time)
                
            results[query_name] = {
                'mean_time': np.mean(times),
                'std_time': np.std(times),
                'min_time': min(times),
                'max_time': max(times)
            }
            
        return results
        
    def save_results(self, benchmark_name: str):
        """Save benchmark results to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.output_dir / f"benchmark_{benchmark_name}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=4)
            
        logger.info(f"Benchmark results saved to {filename}")
        
    def get_system_info(self) -> Dict:
        """Get system information for benchmarking context."""
        cpu_info = {
            'cpu_count': psutil.cpu_count(),
            'cpu_freq': psutil.cpu_freq()._asdict(),
            'cpu_percent': psutil.cpu_percent(interval=1, percpu=True)
        }
        
        memory_info = {
            'total': psutil.virtual_memory().total / (1024**3),  # GB
            'available': psutil.virtual_memory().available / (1024**3),  # GB
            'percent': psutil.virtual_memory().percent
        }
        
        gpu_info = []
        try:
            gpus = GPUtil.getGPUs()
            for gpu in gpus:
                gpu_info.append({
                    'id': gpu.id,
                    'name': gpu.name,
                    'memory_total': gpu.memoryTotal,
                    'memory_used': gpu.memoryUsed,
                    'temperature': gpu.temperature
                })
        except:
            pass
            
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': cpu_info,
            'memory': memory_info,
            'gpu': gpu_info
        } 