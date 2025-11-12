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

## Implemented on **Azure**

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


## How to test the pipelines

This section explains, step-by-step, how to run and validate the three pipelines in Azure DevOps: **IaC (create infra)**, **CI (build image)** and **CD (deploy app)**. It includes the exact checks and commands you should execute to confirm the resources and the application are working.

### Prerequisites
- An Azure subscription (Pay-As-You-Go) and an Azure DevOps organization with project access.  
- An Azure DevOps **Service Connection** (Azure Resource Manager - service principal) authorized for the project.  
- An agent available for pipeline execution:
  - Preferably a Microsoft-hosted agent (requires parallelism grant), or
  - A self-hosted agent registered in an agent pool (recommended to avoid hosted parallelism limits).  
- `az` CLI (locally or via Cloud Shell) and `kubectl` installed for manual validation, or use the Azure Cloud Shell from the portal.

> Pipeline variable names used below: `azureServiceConnection`, `resourceGroup`, `aksName`, `acrName`, `storageAccount`, `containerName`, `imageFullName`.

---

### 1) Run the IaC pipeline (create infra)
Pipeline file: `iac/azure-pipelines-iac.yml`

**What it does**
- Creates the Resource Group, Storage Account + Blob Container, ACR and AKS (selectable via checkboxes).  
- Optionally uploads a sample `index.html` to the blob container.

**How to run (Azure DevOps UI)**
1. Pipelines / New pipeline / select repo / Existing Azure Pipelines YAML / choose `iac/azure-pipelines-iac.yml`.  
2. In the pipeline definition screen, set these variables (or via the run dialog):
   - `azureServiceConnection` / select your Service Connection (e.g. `Azure-Free-Tier-Connection`).
   - `location` (e.g. `eastus`), `resourceGroup` (e.g. `rg-cloudservices-demo`), `storageAccount`, `containerName`, `acrName`, `aksName`.
3. Click **Run pipeline**. The run dialog will show the boolean checkboxes:
   - `createRG`, `createStorage`, `createContainer`, `createACR`, `createAKS`
   - Mark all that you want to create (for the first run mark all).
4. Start the run.

**What to expect in logs**
- Messages like:
  - `Creating resource group: <name>`
  - `Creating storage account: <name>`
  - `Creating ACR: <name>`
  - `Creating AKS cluster: <name>`
- Final confirmation: each task should print `created successfully`.

**Manual validations (after pipeline completes)**
Run in Azure CLI (or use Portal):

```bash
# verify resource group
az group show -n <resourceGroup>

# storage account
az storage account show -n <storageAccount> -g <resourceGroup>

# list blobs (requires az storage commands; use --auth-mode login)
az storage blob list --account-name <storageAccount> -c <containerName> -o table

# ACR
az acr show -n <acrName> -g <resourceGroup>

# AKS
az aks show -n <aksName> -g <resourceGroup>
az aks get-credentials -n <aksName> -g <resourceGroup>
kubectl get nodes
