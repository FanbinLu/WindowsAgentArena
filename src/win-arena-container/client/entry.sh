#!/bin/bash

# Fix for Azure ML Job not using the correct root path
cd /

echo "Starting WinArena..."

# agent="cot"
# model="gpt-4o"

agent="cot_qwen2vl"
model="cot_qwen2vl"
result_dir="./results_tests"
# result_dir="./results_tasks_evaluation/"
worker_id="0"
num_workers="1"
trial_id="1"
# json_name="tasks_windows/tasks.json"
# json_dir="tasks_windows"
json_name="evaluation_examples_windows/test_all.json"
json_dir="evaluation_examples_windows"
worker_ip="http://10.1.1.3:9000/v1"
grounding_model="ui-tars"
grounding_server="http://10.1.1.3:8001/v1"
max_steps=20

# parse agent argument
while [[ $# -gt 0 ]]; do
    case "$1" in
        --agent)
            agent=$2
            shift 2
            ;;
        --model)
            model=$2
            shift 2
            ;;
        --worker-id)
            worker_id=$2
            shift 2
            ;;
        --num-workers)
            num_workers=$2
            shift 2
            ;;
        --result-dir)
            result_dir=$2
            shift 2
            ;;
        --json-name)
            json_name=$2
            shift 2
            ;;
        --diff-lvl)
            diff_lvl=$2  
            shift 2  
            ;;              
        --trial-id)
            trial_id=$2
            shift 2
            ;;
        --worker-ip)
            worker_ip=$2
            shift 2
            ;;
        --max-steps)
            max_steps=$2
            shift 2
            ;;
        --grounding-model)
            grounding_model=$2
            shift 2
            ;;
        --grounding-server)
            grounding_server=$2
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --agent <agent>                 The agent to use (default: navi)"
            echo "  --model <model>                 The model to use (default: gpt-4-vision-preview, available options are: gpt-4o-mini, gpt-4-vision-preview, gpt-4o, gpt-4-1106-vision-preview)"
            echo "  --som-origin <som_origin>       The SoM (Set-of-Mark) origin to use (default: oss, available options are: oss, a11y, mixed-oss)"
            echo "  --a11y-backend <a11y_backend>   The a11y accessibility backend to use (default: uia, available options are: uia, win32)"
            echo "  --clean-results <bool>          Clean the results directory before running the client (default: true)"
            echo "  --worker-id <id>                The worker ID"
            echo "  --num-workers <num>             The number of workers"
            echo "  --result-dir <dir>              The directory to store the results (default: ./results)"
            echo "  --json-name <name>              The name of the JSON file to use (default: test_all.json)"
            echo "  --diff-lvl <level>              The difficulty level of benchmark (default: normal, available options are: normal, hard)"  
            exit 0
            ;;
        *)
    esac
done

# copy the VM storage to local storage
cp /storage/* /storage_local/
export STORAGE=/storage_local

# Starts the VM and blocks until the Windows Arena Server is ready
echo "Starting VM..."
./entry_setup.sh
echo "VM started, server ready"


cd /client

echo "Starting client..."

bash start_single.sh \
    --num-workers $num_workers \
    --worker-id $worker_id \
    --worker-ip $worker_ip \
    --result-dir $result_dir \
    --agent $agent \
    --model $model \
    --max-steps $max_steps \
    --json-name $json_name \
    --grounding-model $grounding_model \
    --grounding-server $grounding_server \
    --json-dir $json_dir \
    --trial-id $trial_id 