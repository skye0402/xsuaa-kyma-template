# Gradio on SAP BTP Kyma

This project demonstrates how to deploy a Python Gradio application to SAP Business Technology Platform (BTP) Kyma, which is a Kubernetes-based runtime.

## Prerequisites

- SAP BTP Kyma environment
- Docker image of the Gradio application
- Access to the SAP BTP service marketplace
- `kubectl` and `helm` CLI tools installed
- Access to a terminal or command line interface

## Deployment Steps

1. **Create a Namespace**:
   Create a namespace in your Kyma environment for the Gradio application.

   ```yaml
   apiVersion: v1
   kind: Namespace
   metadata: 
    name: gunter-xsuaa2
    labels:
      istio-injection: enabled
   ```

2. **Deploy XSUAA Service**:
   Deploy the XSUAA service instance and binding to secure the application.

   ```yaml
   # Service Instance
   apiVersion: services.cloud.sap.com/v1alpha1
   kind: ServiceInstance
   # ... (rest of the service instance configuration)
   
   # Service Binding
   apiVersion: services.cloud.sap.com/v1alpha1
   kind: ServiceBinding
   # ... (rest of the service binding configuration)
   ```

3. **Create Service Account**:
   Define a service account for the deployment.

   ```yaml
   apiVersion: v1
   kind: ServiceAccount
   # ... (rest of the service account configuration)
   ```

4. **Deploy Gradio Service and App**:
   Deploy the Gradio service and app using the provided Docker image.

   ```yaml
   # Service
   apiVersion: v1
   kind: Service
   # ... (rest of the service configuration)
   
   # Deployment
   apiVersion: apps/v1
   kind: Deployment
   # ... (rest of the deployment configuration)
   ```

5. **Persistent Volume Claim**:
   Create a persistent volume claim if your application requires storage.

   ```yaml
   kind: PersistentVolumeClaim
   apiVersion: v1
   # ... (rest of the persistent volume claim configuration)
   ```

6. **Configure Routing**:
   Set up the destination rule and API rule for routing within the Kyma environment.

   ```yaml
   # Destination Rule
   apiVersion: networking.istio.io/v1alpha3
   kind: DestinationRule
   # ... (rest of the destination rule configuration)
   
   # API Rule
   apiVersion: gateway.kyma-project.io/v1beta1
   kind: APIRule
   # ... (rest of the API rule configuration)
   ```

7. **Deploy AppRouter**:
   Deploy the AppRouter to handle authentication and routing to the Gradio app.

   ```yaml
   # Deployment
   apiVersion: apps/v1
   kind: Deployment
   # ... (rest of the AppRouter deployment configuration)
   
   # Service
   apiVersion: v1
   kind: Service
   # ... (rest of the AppRouter service configuration)
   ```

8. **ConfigMaps**:
   Create ConfigMaps for the destinations and XSUAA configuration.

   ```yaml
   # Destinations ConfigMap
   apiVersion: v1
   kind: ConfigMap
   # ... (rest of the destinations ConfigMap configuration)
   
   # XSUAA ConfigMap
   apiVersion: v1
   kind: ConfigMap
   # ... (rest of the XSUAA ConfigMap configuration)
   ```

9. **Run the Application**:
   Execute the Python script to run the Gradio application.

   ```python
   # ... (Python Gradio application code)
   ```

## Running the Application

To run the application, execute the Python script provided in the "Program" section of this README. Ensure that the necessary environment variables are set before running the script.

## Additional Information

The application uses JWT for authentication and logs user data to a SQLite database. It also features a custom carousel and a user info tab that displays login counts.

For more detailed instructions and configurations, refer to the YAML files and Python code provided.

## Support

If you encounter any issues or require assistance, please open an issue on the GitHub repository.

---

**Note**: This README is a general guide. Please adjust the commands and configurations to match your specific setup and requirements.
