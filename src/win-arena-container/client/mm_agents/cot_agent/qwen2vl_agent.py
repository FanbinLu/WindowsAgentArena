import json
import os
import logging
import re
from typing import Union, Dict, List
# from mm_agents.planner.computer import Computer, WindowManager
import copy
import base64
import io
from io import BytesIO

from PIL import Image, ImageDraw

from openai import OpenAI

from .output_parser import  Qwen2VLParser, UITarsGroundModel

logger = logging.getLogger("desktopenv.agent")

def prev_actions_to_string(prev_actions, n_prev=3):  
    result = ""  
    n_prev = min(n_prev, len(prev_actions))  # Limit n_prev to the length of the array  
    for i in range(1, n_prev + 1):  
        action = prev_actions[-i]  # Get the element at index -i (from the end)  
        result += f"Screen is currently at time step T. Below is the action executed at time step T-{i}: \n{action}\n\n"  
    return result  

from PIL import Image



class CoTQwen2VLAgent():
    system_prompt = '''You are STEVE, an AI that completes tasks on a user's computer with mouse and keyboard operations. Your role as an assistant involves thoroughly exploring the user task through a systematic long thinking process before providing the final precise and accurate solutions. This requires engaging in a comprehensive cycle of screenshot analysis, action reflection, task planning and error backtracing to complete the user task step-by-step. Please structure your response into two main sections: Thought and Solution. In the Thought section, detail your reasoning process using the specified format: <|begin_of_thought|> thought <|end_of_thought|> Each step should include detailed considerations such as screenshot analysis, summarizing relevant findings, brainstorming new ideas, verifying the accuracy of the current steps, refining any errors, and revisiting previous steps. In the Solution section, based on various attempts, explorations, and reflections from the Thought section, systematically present the final solution that you deem correct. The solution should remain a logical, accurate, concise expression style and detail necessary step needed to reach the conclusion, formatted as follows: <|begin_of_solution|> {thoughts, rationale, decision, python(optional)} <|end_of_solution|>"""

You can use the following functions:
```python
computer.mouse.move(<|object_ref_start|>"target_element"<|object_ref_end|><|point_start|>(x,y)<|point_end|>)
computer.mouse.single_click()
computer.mouse.double_click()
computer.mouse.right_click() 
computer.mouse.scroll(dir="up/down")
computer.mouse.drag(<|object_ref_start|>"target_element"<|object_ref_end|><|point_start|>(x,y)<|point_end|>) # drag from current cursor position to the element

computer.keyboard.write("text")
computer.keyboard.press("key") # press a key once (donw and up)
computer.keyboard.keyDown("key") # press and hold a key
computer.keyboard.keyUp("key") # release a key
computer.keyboard.hotkey("key1", "key2", ...) # press multiple keys simultaneously to trigger a shortcut

```
    '''
    def __init__(
            self,
            server, 
            model: str = "cot_qwen2vl",
            grounding_server: str = "http://10.1.1.3:8001/v1",
            grounding_model: str = "ui-tars",
            obs_view = "screen", # "screen" or "window"
            auto_window_maximize = False,
            temperature: float = 0.5,
    ):
        self.action_space = "code_block"
        self.server = server
        self.model = model
        
        print(self.model, self.server)
        self.obs_view = obs_view
        self.auto_window_maximize = auto_window_maximize
        self.prev_window_title = None
        self.prev_window_rect = None

        self.client = OpenAI(
            base_url=server,
            api_key="empty",
        )

        self.parser = Qwen2VLParser()
        self.ground_model = UITarsGroundModel(
            server=grounding_server,
            model=grounding_model,
            input_format='qwen2vl'
        )

        self.n_prev = 30
        self.step_counter = 0

        self.history_images = []
        self.history_images = []
        self.history_messages = []

    def get_base64_payload(self, base64_image: str, detail="auto") -> dict:  
        return {  
            "type": "image_url",  
            "image_url": {  
                "url": f"data:image/jpeg;base64,{base64_image}",  
                "detail": detail 
            }  
        }  

    def encode_image(self, image: Union[str, Image.Image]) -> str:  
        if isinstance(image, str):  
            with open(image, "rb") as image_file:  
                return base64.b64encode(image_file.read()).decode("utf-8")  
        elif isinstance(image, Image.Image):  
            buffer = io.BytesIO()  
            # convert to rgb if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")
            image.save(buffer, format="JPEG")  
            return base64.b64encode(buffer.getvalue()).decode("utf-8")  

    def predict(self, instruction: str, obs: Dict) -> List:
        """
        Predict the next action(s) based on the current observation.
        """
        logs={}
        
        if self.obs_view == "screen":
            image_file = BytesIO(obs['screenshot'])
            view_image = Image.open(image_file)
            view_rect = [0, 0, view_image.width, view_image.height]
        else:
            view_image = obs['window_image']
            view_rect = obs['window_rect']
        
        window_title, window_names_str, window_rect, computer_clipboard = obs['window_title'], obs['window_names_str'], obs['window_rect'], obs['computer_clipboard']
        original_h, original_w = view_image.height, view_image.width
        
        image = view_image 
                
        logs['window_title'] = window_title
        logs['window_names_str'] = window_names_str
        logs['computer_clipboard'] = computer_clipboard
        logs['image_width'] = image.width
        logs['image_height'] = image.height


        logger.info(f"Thinking...")
        
        # check if the last message is from the assistant
        if len(self.history_messages) > 0 and self.history_messages[-1]['role'] != 'assistant':
            logger.info(f"Error in history_message. Seems like the last message is not from the assistant. Remove the last message.")
            self.history_messages = self.history_messages[:-1]
                    
        message_context = copy.deepcopy(self.history_messages[-self.n_prev*2:])

        query_message = {
            "role": "user",
            "content": [
                self.get_base64_payload(self.encode_image(view_image)),
                {"type": "text", "text": f'Task: {instruction}. Please generate the next move.'}
            ],
        }

        message_context.append(copy.deepcopy(query_message))
        self.history_messages.append(copy.deepcopy(query_message))

        # add system_prompt
        message_context[0]["content"].insert(0, {"type": "text", "text": self.system_prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=message_context,
            frequency_penalty=0.0, # do not use too large value because it will result in action format error
            temperature=0.6,
            max_tokens=4096,
            extra_body={"skip_special_tokens": False}
        )
        plan_result_full = response.choices[0].message.content
        print(plan_result_full)

        plan_result = re.search(r'<\|begin_of_solution\|>(.*)<\|end_of_solution\|>', plan_result_full, re.DOTALL)
        if plan_result:
            plan_result = plan_result.group(1)
        else:
            logger.info(f"Error in plan_result. Cannot find the plan_result.")
            plan_result = plan_result_full
        

        decision_block, actions = self.parser.parse(plan_result)
        if actions in ['DONE', 'FAIL', 'WAIT', 'CALL_USER', 'RESET']:
            actions_grounded = actions
        else:
            actions_grounded, positions = self.ground_model.ground_action(view_image, actions)

        logs['plan_result_full'] = plan_result_full
        logs['actions'] = actions
        logs['actions_grounded'] = actions_grounded
        logs['plan_result'] = plan_result

        response = ""
        computer_update_args = {
            'rects': [view_rect],
            'window_rect': view_rect,
            'screenshot': view_image,
            'scale': 1.0,
            'clipboard_content': computer_clipboard,
            'swap_ctrl_alt': False
        }

        self.step_counter += 1
        self.history_images.append(view_image)
        self.history_actions.append(plan_result)
        self.history_messages.append({
            "role": "assistant",
            "content": [
                {"type": "text", "text": plan_result_full}
            ]
        })

        actions = [actions_grounded] # to list[str]
        return response, actions, logs, computer_update_args


    def reset(self):
        self.prev_window_title = None
        self.prev_window_rect = None
        self.clipboard_content = None
        self.step_counter = 0
        self.history_images = []
        self.history_actions = []
        self.history_messages = []
    
    