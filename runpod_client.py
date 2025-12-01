"""
RunPod API Client
This script demonstrates how to connect to and interact with RunPod.
"""

import requests
import json
import time
from typing import Dict, Any, Optional
from runpod_config import RunPodConfig

class RunPodClient:
    """Client for interacting with RunPod API."""
    
    def __init__(self, config: RunPodConfig):
        self.config = config
        if not config.validate():
            raise ValueError("Invalid RunPod configuration")
    
    def run_inference(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run inference on a RunPod endpoint.
        
        Args:
            input_data: The input data for the model
            
        Returns:
            The response from the RunPod API
        """
        url = f"{self.config.api_base_url}/graphql"
        
        # GraphQL query for running inference
        query = """
        mutation RunInference($input: RunPodInput!) {
            runPodInference(input: $input) {
                id
                status
                output
                error
            }
        }
        """
        
        variables = {
            "input": {
                "endpointId": self.config.endpoint_id,
                "input": input_data
            }
        }
        
        payload = {
            "query": query,
            "variables": variables
        }
        
        try:
            response = requests.post(
                url,
                headers=self.config.get_headers(),
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error running inference: {e}")
            return {"error": str(e)}
    
    def get_pod_status(self) -> Dict[str, Any]:
        """Get the status of your RunPod endpoint."""
        url = f"{self.config.api_base_url}/graphql"
        
        query = """
        query GetPodStatus($endpointId: String!) {
            podStatus(endpointId: $endpointId) {
                id
                status
                runtime
                uptime
                cost
            }
        }
        """
        
        variables = {
            "endpointId": self.config.endpoint_id
        }
        
        payload = {
            "query": query,
            "variables": variables
        }
        
        try:
            response = requests.post(
                url,
                headers=self.config.get_headers(),
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error getting pod status: {e}")
            return {"error": str(e)}
    
    def wait_for_completion(self, job_id: str, max_wait_time: int = 300) -> Dict[str, Any]:
        """
        Wait for a job to complete.
        
        Args:
            job_id: The ID of the job to wait for
            max_wait_time: Maximum time to wait in seconds
            
        Returns:
            The final job result
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            # Check job status
            url = f"{self.config.api_base_url}/graphql"
            
            query = """
            query GetJobStatus($jobId: String!) {
                jobStatus(jobId: $jobId) {
                    id
                    status
                    output
                    error
                }
            }
            """
            
            variables = {"jobId": job_id}
            payload = {"query": query, "variables": variables}
            
            try:
                response = requests.post(
                    url,
                    headers=self.config.get_headers(),
                    json=payload,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get("data", {}).get("jobStatus", {}).get("status") in ["COMPLETED", "FAILED"]:
                    return result
                
                print(f"⏳ Job {job_id} is still running...")
                time.sleep(5)  # Wait 5 seconds before checking again
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Error checking job status: {e}")
                return {"error": str(e)}
        
        return {"error": "Job did not complete within the specified time"}

def main():
    """Example usage of the RunPod client."""
    print("🚀 RunPod Connection Example")
    print("=" * 40)
    
    # Load configuration
    config = RunPodConfig()
    
    if not config.validate():
        print("\n❌ Please set your RunPod API credentials:")
        print("1. Set RUNPOD_API_KEY environment variable")
        print("2. Set RUNPOD_ENDPOINT_ID environment variable")
        print("\nYou can also create a .env file with:")
        print("RUNPOD_API_KEY=your_api_key_here")
        print("RUNPOD_ENDPOINT_ID=your_endpoint_id_here")
        return
    
    try:
        # Create client
        client = RunPodClient(config)
        print("✅ RunPod client created successfully")
        
        # Get pod status
        print("\n📊 Checking pod status...")
        status = client.get_pod_status()
        print(f"Pod Status: {json.dumps(status, indent=2)}")
        
        # Example inference (uncomment and modify as needed)
        # print("\n🤖 Running inference...")
        # input_data = {"prompt": "Hello, world!"}
        # result = client.run_inference(input_data)
        # print(f"Inference Result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

