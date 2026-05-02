#!/bin/bash
# Local Spark Cluster Setup

echo "🔥 Setting up local Spark cluster..."

# Start Spark master
echo "Starting Spark master..."
$SPARK_HOME/sbin/start-master.sh

# Start Spark worker
echo "Starting Spark worker..."
$SPARK_HOME/sbin/start-worker.sh spark://localhost:7077

# Wait for cluster to be ready
sleep 5

echo "✅ Spark cluster ready!"
echo "📊 Master UI: http://localhost:8080"
echo "🔗 Spark URL: spark://localhost:7077"
