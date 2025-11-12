# Cloud Services – Technical Project  
**Author:** Erick Colina  
**Date:** November 2025  
**Cloud Provider Chosen:** Microsoft Azure  

---

## Problem Statement (from the technical test)

With this existing setup:
- An AWS account
- A healthy Kubernetes cluster running in an AWS region (it doesn’t matter if it’s multi-AZ or not)

The Cloud Services team would like to expose the contents of an S3 bucket through a Kubernetes Ingress resource.

### Requirements
- Create a Kubernetes workload that exposes the content of a private S3 bucket through a Kubernetes Ingress.  
- The content of the S3 bucket should be mapped at the root level of the Ingress FQDN.  
- Add a `README.md` (500–700 words) explaining how to test, use, and implement the solution.

### Bonus points
- Kubernetes manifests or Helm charts.  
- No AWS API keys.  
- JSON logging of the HTTP requests.  
- Steps to set up CI/CD pipeline.

---

## Approach and Rationale: Implemented on **Azure**

Although the challenge was originally designed for AWS, I implemented it using **Azure** for the following reasons:

1. **Free Cloud Credits:** Azure provides **200 USD of free credit** upon creating a new account, even for educational accounts, without requiring a credit card.  
2. **Free-tier compatibility:** Azure allows creating a managed Kubernetes cluster (AKS) and a container registry (ACR) at low or zero cost within the free tier.  
3. **Simplified DevOps integration:** Azure DevOps integrates natively with Azure resources and supports end-to-end automation using YAML pipelines and service connections.  

This approach replicates the same logic proposed in the AWS version but fully within Azure’s ecosystem:

- Instead of **S3**, i use **Azure Blob Storage**.  
- Instead of **EKS**, i use **Azure Kubernetes Service (AKS)**.  
- Instead of **IAM roles**, i use **Managed Identity** for secure access to private storage.  

---

## Solution Overview

The goal is to expose the contents of a **private Azure Blob Storage container** through a **Kubernetes Ingress** hosted in AKS.  
To achieve this, I built the following logical structure:

Azure Resource Group
Azure Container Registry (ACR)
Azure Kubernetes Service (AKS)
Azure Storage Account (Blob)
Application Deployment via Helm Chart


### Components

| Component | Purpose |
|------------|----------|
| **Azure Blob Storage** | Hosts private content to be served through the API |
| **.NET API container** | Reads blob content and serves it as HTTP responses |
| **Kubernetes Deployment & Service** | Deploys the container in AKS |
| **Ingress Controller** | Routes external traffic to the pod through an HTTP endpoint |
| **Helm Chart** | Simplifies deployment configuration and parameterization |
| **Azure DevOps Pipelines** | Automates provisioning, build, and deployment processes |

---

## Infrastructure Setup (IaC Pipeline)

I use **Azure CLI** within an Azure DevOps YAML pipeline.  
The pipeline (`azure-pipelines-iac.yml`) allows selecting — via parameters and checkboxes — which components to create:

- Resource Group  
- Azure Container Registry (ACR)  
- Azure Kubernetes Service (AKS)  
- Azure Storage Account  
- Optional: Sample container deployment  

Each stage depends on the success of the previous one.  

This approach allows full automation from Azure DevOps and keeps the solution inside the free-tier boundary.

---

## Continuous Integration (CI)

**Pipeline:** `pipelines/azure-pipelines-ci.yml`  

The CI pipeline builds and publishes the container image to the Azure Container Registry.  
Main steps:

1. **Authenticate with Azure** using a service connection.  
2. **Login to ACR.**  
3. **Build Docker image** from the `/app` folder.  
4. **Push image to ACR.**  
5. **Publish the image reference** (`imageFullName`) as a pipeline variable for the CD stage.  

**Logging:**  
Each step outputs clear logs like:  
"Building Docker image: myacr.azurecr.io/aks-blob-proxy:123"  
"Pushing image to ACR..."  

---

## Continuous Deployment (CD)

**Pipeline:** `pipelines/azure-pipelines-cd.yml`  

This pipeline deploys the latest container to the AKS cluster using Helm.  
Main steps:

1. **Authenticate with Azure** via the same service connection.  
2. **Retrieve AKS credentials** (`az aks get-credentials`).  
3. **Manual Approval Gate** (ManualValidation) before deployment.  
4. **Helm Deploy** to AKS using:helm upgrade