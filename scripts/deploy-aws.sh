#!/bin/bash
# Production deployment to AWS EKS

set -e

echo "☁️  STRATUM PROTOCOL - AWS EKS Deployment"
echo "========================================="

AWS_REGION="${AWS_REGION:-us-east-1}"
CLUSTER_NAME="stratum-production"

# Create EKS cluster
echo "Creating EKS cluster..."
eksctl create cluster \
  --name $CLUSTER_NAME \
  --region $AWS_REGION \
  --nodegroup-name stratum-nodes \
  --node-type m5.2xlarge \
  --nodes 10 \
  --nodes-min 5 \
  --nodes-max 50 \
  --managed

# Update kubeconfig
aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME

# Install AWS Load Balancer Controller
echo "Installing AWS Load Balancer Controller..."
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"

helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=$CLUSTER_NAME \
  --set serviceAccount.create=true \
  --set serviceAccount.name=aws-load-balancer-controller

# Deploy application
echo "Deploying STRATUM PROTOCOL..."
./deploy.sh production

echo "✅ AWS EKS Deployment Complete!"
echo ""
echo "Get LoadBalancer URL:"
echo "  kubectl get svc frontend -n stratum-protocol"
