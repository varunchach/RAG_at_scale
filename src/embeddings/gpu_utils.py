# GPU Scheduling and Resource Management
import torch
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class GPUManager:
    @staticmethod
    def get_gpu_info():
        """Get GPU information"""
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            current_device = torch.cuda.current_device()

            info = []
            for i in range(device_count):
                props = torch.cuda.get_device_properties(i)
                info.append({
                    'device_id': i,
                    'name': props.name,
                    'total_memory': props.total_memory / 1024**3,  # GB
                    'major': props.major,
                    'minor': props.minor
                })

            return {
                'available': True,
                'device_count': device_count,
                'current_device': current_device,
                'devices': info
            }
        else:
            return {'available': False}

    @staticmethod
    def set_device(device_id: Optional[int] = None):
        """Set CUDA device"""
        if torch.cuda.is_available():
            if device_id is not None and device_id < torch.cuda.device_count():
                torch.cuda.set_device(device_id)
                logger.info(f"Set CUDA device to {device_id}")
            else:
                logger.info("Using default CUDA device")
        else:
            logger.warning("CUDA not available")

    @staticmethod
    def get_memory_usage():
        """Get GPU memory usage"""
        if torch.cuda.is_available():
            return {
                'allocated': torch.cuda.memory_allocated() / 1024**3,  # GB
                'reserved': torch.cuda.memory_reserved() / 1024**3,    # GB
                'max_allocated': torch.cuda.max_memory_allocated() / 1024**3  # GB
            }
        return None

    @staticmethod
    def clear_cache():
        """Clear GPU cache"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("GPU cache cleared")
