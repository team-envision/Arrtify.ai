# -*- coding: utf-8 -*-
"""MultilingualTextToImageGenerator.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1sqE9iUoHTYeLWq7SzkHEf6c2V1Q2PqrQ
"""

!pip install googletrans==3.1.0a0
!pip install --upgrade diffusers transformers accelerate -q
!pip install git+https://github.com/openai/CLIP.git
!pip install scikit-image
!pip install ipywidgets

from googletrans import Translator
import torch
from diffusers import StableDiffusionPipeline
import clip
from PIL import Image
from skimage.metrics import structural_similarity as ssim
import numpy as np
import ipywidgets as widgets
from IPython.display import display
from IPython.display import display, clear_output

class CFG:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    seed = 42
    generator = torch.Generator(device).manual_seed(seed)
    image_gen_steps = 35
    image_gen_model_id = "stabilityai/stable-diffusion-2"
    image_gen_size = (900, 900)
    image_gen_guidance_scale = 9

image_gen_model = StableDiffusionPipeline.from_pretrained(
    CFG.image_gen_model_id, torch_dtype=torch.float16,
    revision="fp16", use_auth_token='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', guidance_scale=9
)
image_gen_model = image_gen_model.to(CFG.device)

def generate_image(prompt, model):
    image = model(
        prompt, num_inference_steps=CFG.image_gen_steps,
        generator=CFG.generator,
        guidance_scale=CFG.image_gen_guidance_scale
    ).images[0]

    image = image.resize(CFG.image_gen_size)
    return image

def get_translation(text, dest_lang):
    translator = Translator()
    translated_text = translator.translate(text, dest=dest_lang)
    return translated_text.text

device = "cuda" if torch.cuda.is_available() else "cpu"
clip_model, preprocess = clip.load("ViT-B/32", device=device)

def calculate_clip_score(prompt, image):
    image = preprocess(image).unsqueeze(0).to(device)
    text = clip.tokenize([prompt]).to(device)

    with torch.no_grad():
        image_features = clip_model.encode_image(image)
        text_features = clip_model.encode_text(text)

    image_features /= image_features.norm(dim=-1, keepdim=True)
    text_features /= text_features.norm(dim=-1, keepdim=True)

    similarity = (image_features @ text_features.T).item()
    return similarity

def calculate_ssim(image1, image2):
    image1 = np.array(image1.convert('L'))
    image2 = np.array(image2.convert('L'))
    score, _ = ssim(image1, image2, full=True)
    return score

text_input = widgets.Text(
    value='',
    placeholder='Type something',
    description='Prompt:',
    disabled=False
)
generate_button = widgets.Button(
    description='Generate Image',
    disabled=False,
    button_style='',  # 'success', 'info', 'warning', 'danger' or ''
    tooltip='Click me',
    icon='check'
)

clear_button = widgets.Button(
    description='Clear',
    disabled=False,
    button_style='danger',  # 'success', 'info', 'warning', 'danger' or ''
    tooltip='Clear all outputs',
    icon='times'
)
def on_generate_button_clicked(b):
    generate_and_evaluate(text_input.value)

def on_clear_button_clicked(b):
    clear_output()
    display(text_input)
    display(generate_button)
    display(clear_button)

generate_button.on_click(on_generate_button_clicked)
clear_button.on_click(on_clear_button_clicked)

display(text_input)
display(generate_button)
display(clear_button)

def generate_and_evaluate(prompt):
    translated_prompt = get_translation(prompt, "en")
    generated_image = generate_image(translated_prompt, image_gen_model)
    display(generated_image)

    clip_score = calculate_clip_score(translated_prompt, generated_image)
    print(f"CLIP Score: {clip_score}")
    reference_image = Image.new('RGB', CFG.image_gen_size, color='white')

    ssim_score = calculate_ssim(generated_image, reference_image)
    print(f"SSIM: {ssim_score}")