"""Script to run & evaluate agent-loop on a single example from the benchmark."""
import datetime
import json
import logging
import os
import time
import traceback
from trajectory_recorder import TrajectoryRecorder

import signal

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Function execution timed out")

def run_with_timeout(func, timeout, max_retries, *args, **kwargs):
    retries = 0

    while retries < max_retries:
        # Set the timeout signal
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)  # Set alarm for timeout seconds

        try:
            result = func(*args, **kwargs)
            signal.alarm(0)  # Cancel alarm if function succeeds
            return result
        except TimeoutError:
            retries += 1
            print(f"Timeout occurred! Retrying {retries}/{max_retries}...")
        except Exception as e:
            signal.alarm(0)  # Cancel alarm in case of other exceptions
            raise e

    raise RuntimeError(f"Function failed after {max_retries} retries due to timeouts.")


logger = logging.getLogger("desktopenv.experiment")

# Open the JSON file
with open("./settings.json", "r") as file:
    # Load the JSON data from the file
    data = json.load(file)
time_limit = data["time_limit"]

def run_single_example(agent, env, example, max_steps, instruction, args, example_result_dir, scores):
    agent.reset()
    # obs = run_with_timeout(env.reset(task_config=example), timeout=200, max_retries=3) # 200s and retry 3 times
    obs = run_with_timeout(env.reset, timeout=200, max_retries=3, task_config=example) # 200s and retry 3 times

    done = False
    step_idx = 0

    #env.controller.start_recording()
    start_time = datetime.datetime.now()
    
    # Initialize recorder, which will save the trajectory as a JSON & HTML in {example_result_dir}/traj.(jsonl,html)
    recorder = TrajectoryRecorder(example_result_dir)
    
    # Record initial state
    init_timestamp = start_time.strftime("%Y%m%d@%H%M%S")
    recorder.record_init(obs, example, init_timestamp)
    
    while not done and step_idx < max_steps:
        if obs is None:
            logger.error("Observation is None. Waiting a little to do next step.")
            time.sleep(5)
            step_idx += 1
            continue

        logger.info("Agent: Thinking...")
        response, actions, logs, computer_update_args = agent.predict(
            instruction,
            obs
        )

        # update the computer object, used by navi's action space
        if computer_update_args:
            env.controller.update_computer(**computer_update_args)
        
        # step environment with agent actions 
        for action in actions:
            # Capture the timestamp before executing the action
            action_timestamp = datetime.datetime.now().strftime("%Y%m%d@%H%M%S")
            elapsed_timestamp = f"{datetime.datetime.now() - start_time}"
            logger.info("Step %d: %s", step_idx + 1, action)
            
            print('sleep: ', args.sleep_after_execution)
            obs, reward, done, info = env.step(action, args.sleep_after_execution)

            logger.info("Reward: %.2f", reward)
            logger.info("Done: %s", done)
            
            # Record step data
            recorder.record_step(
                obs, 
                logs,
                step_idx,
                action_timestamp,
                elapsed_timestamp,
                action,
                reward,
                done,
                info
            )

            if done:
                logger.info("The episode is done.")
                break
        # inc step counter
        step_idx += 1
    
    logger.info("Running evaluator(s)...")
    # result = env.evaluate()
    result = run_with_timeout(env.evaluate, timeout=200, max_retries=3)
    logger.info("Result: %.2f", result)
    scores.append(result)

    with open(os.path.join(example_result_dir, "result.txt"), "w", encoding="utf-8") as f:
        f.write(f"{result}\n")
    
    # Record final results
    recorder.record_end(result, start_time)
    # env.controller.end_recording(os.path.join(example_result_dir, "recording.mp4"))