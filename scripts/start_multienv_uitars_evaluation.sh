#!/bin/bash

# Total number of tasks
TOTAL_TASKS=28

# Number of workers
WORKERS=7

# Function to execute tasks by a worker
run_worker_tasks() {
  local worker_id=$1
  local total_tasks=$2
  local workers=$3
  local trial_id=$4

  echo "Starting worker $worker_id"

  # Each worker handles tasks where task_id % workers == worker_id
  for ((task_id = worker_id; task_id < total_tasks; task_id += workers)); do
    echo "Worker $worker_id executing task $task_id"
    worker_ip="http://10.1.1.3:$((worker_id + 9000))/v1"

    docker run --rm -p $((worker_id + 8006)):8006 -p $((worker_id + 3390)):3389 --name winarena_$worker_id --platform linux/amd64 --device=/dev/kvm -e RAM_SIZE=8G -e CPU_CORES=8 -v /gpfs/lufanbin/projects/WindowsAgentArena/src/win-arena-container/vm/storage/.:/storage -v /gpfs/lufanbin/projects/WindowsAgentArena/src/win-arena-container/vm/setup/.:/shared -v /gpfs/lufanbin/projects/WindowsAgentArena/src/win-arena-container/client/.:/client --cap-add NET_ADMIN --gpus all --stop-timeout 120 --entrypoint /bin/bash -e OPENAI_API_KEY=$OPENAI_API_KEY -e OPENAI_BASE_URL=$OPENAI_BASE_URL windowsarena/winarena-eval:latest -c "bash /client/entry.sh --agent ui-tars --model ui-tars  --worker-id $task_id --num-workers $TOTAL_TASKS --trial-id $trial_id --result-dir results_evaluation/UITARS_origin_7BDPO --max-steps 20 --worker-ip $worker_ip" > "collection_logs/log_${worker_id}_${task_id}.txt" 2>&1
  done

  echo "Worker $worker_id finished"
}

# run_worker_tasks 0 256 8
# exit

# Cleanup function to terminate all background processes
cleanup() {
  echo "Caught SIGINT. Terminating all workers..."
  pkill -P $$    # Kill all child processes of this script
  wait           # Wait for all child processes to exit
  echo "All workers terminated. Exiting."
  exit 1
}

# Trap SIGINT (Ctrl-C) to call the cleanup function
trap cleanup SIGINT



# Start all workers in parallel
for ((worker_id = 0; worker_id < WORKERS; worker_id++)); do
  run_worker_tasks "$worker_id" "$TOTAL_TASKS" "$WORKERS" "0" &
done

# Wait for all workers to finish
wait

echo "All workers have completed their tasks."
