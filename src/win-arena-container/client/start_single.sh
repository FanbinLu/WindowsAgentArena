#!/bin/bash

agent="cot_qwen2vl"
model="gpt-4o"
model="cot_qwen2vl_uitars"
som_origin="oss"
a11y_backend="uia"
observation_type="screenshot"
clean_results="false"
worker_id="0"
num_workers="1"
worker_ip="http://10.1.1.3:8000/v1"
grounding_server="http://10.1.1.3:8001/v1"
grounding_model="ui-tars"
result_dir="./results_tasks_cot_0204"
# result_dir="./results_tasks_evaluation"
# json_name="tasks_windows/tasks.json"
# json_dir="tasks_windows"
json_name="evaluation_examples_windows/test_all.json"
json_dir="evaluation_examples_windows"
# domain="chrome"
domain="all"
diff_lvl="normal"
trial_id="0"
max_steps=30

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
        --som-origin)
            som_origin=$2
            shift 2
            ;;
        --a11y-backend)
            a11y_backend=$2
            shift 2
            ;;
        --clean-results)
            clean_results=$2
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
        --worker-ip)
            worker_ip=$2
            shift 2
            ;;
        --result-dir)
            result_dir=$2
            shift 2
            ;;
        --json-dir)
            json_dir=$2
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
        --max-steps)
            max_steps=$2
            shift 2
            ;;
        --grounding-server)
            grounding_server=$2
            shift 2
            ;;
        --grounding-model)
            grounding_model=$2
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
            echo "  --json-dir <dir>                The directory containing the JSON file (default: ./evaluation_examples_windows)"
            echo "  --diff-lvl <level>              The difficulty level of benchmark (default: normal, available options are: normal, hard)"  
            exit 0
            ;;
        *)
    esac
done

cd /client
# if [ "$clean_results" = true ]; then
#     echo "Cleaning results directory..."
#     rm -rf "$result_dir"/*
# fi

echo "Running agent $agent..."
python run.py \
    --agent "$agent" \
    --model "$model" \
    --som_origin "$som_origin" \
    --a11y_backend "$a11y_backend" \
    --observation_type "$observation_type" \
    --worker_id "$worker_id" \
    --num_workers "$num_workers" \
    --worker_ip "$worker_ip" \
    --grounding_model $grounding_model \
    --grounding_server $grounding_server \
    --result_dir "$result_dir" \
    --test_all_meta_path "$json_name" \
    --test_config_base_dir "$json_dir" \
    --domain "$domain" \
    --trial_id $trial_id \
    --diff_lvl "$diff_lvl" \
    --max_steps $max_steps