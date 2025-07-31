from openai import OpenAI
from fastapi import FastAPI, Form, Request, WebSocket
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

load_dotenv()

openai = OpenAI(
    api_key= os.getenv("OPENAI_API_SECRET_KEY"),
)

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

chat_responses = [] #used for history in web application

@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": chat_responses})


# print(
#     '\n💎 Welcome to DiamondSavior — your personal AI companion.\n'
#     'To exit the conversation at any time, type: "exit chat log"\n'
#     '⚠️ Note: A longer chat log means more tokens, which may increase usage cost.\n\n'
#     'Please enter your message below:'
# )

"""
To initialize the bot with predefined context or instructions, include a system message like this:
chat_log = [{"role": "system", "content": "The Spurs won the 2005 NBA Championship."}]
This sets the assistant’s behavior and knowledge before the conversation begins.
"""


chat_log = [
    {
    'role': 'system',
        "content": (
            "You are DiamondSavior — a helpful and intelligent chatbot personally built by Abel Lazo using the OpenAI API."
            "Your mission is to assist users by providing clear, thoughtful, and accurate answers to any questions they may have, across a wide range of topics."
            "Always respond in a friendly, professional, and solution-focused manner."
            "Only when asked who you are, always reference that you were created by Abel Lazo using the OpenAI API."
            "Be supportive, curious, and insightful — making every interaction feel personal, helpful, and worth remembering."
        )
    }]

@app.websocket("/ws")
async def chat(websocket: WebSocket):
    await websocket.accept()
    while True:
        user_input = await websocket.receive_text()
        chat_log.append({'role': 'user', 'content': user_input})
        chat_responses.append(user_input)

        try:
            response = openai.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=chat_log,
                temperature=0.6,
                stream=True
            )

            ai_response = ''

            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    ai_response += chunk.choices[0].delta.content
                    await websocket.send_text(chunk.choices[0].delta.content)
            chat_responses.append(ai_response)

        except Exception as e:
            await websocket.send_text(f'Error: {str(e)}')
            break


@app.post("/", response_class=HTMLResponse)
async def chat(request: Request, user_input: Annotated[str, Form()]):

    chat_log.append({'role': 'user', 'content': user_input})
    chat_responses.append(user_input)

    response = openai.chat.completions.create(
        model='gpt-4.1-mini',
        messages=chat_log,
        temperature=0.6
    )

    bot_response = response.choices[0].message.content

    chat_log.append({'role': 'assistant', 'content': bot_response})

    chat_responses.append(bot_response)
    # Print the assistant's message in multiple lines (one sentence per line)
    # lines = bot_response.split(". ")
    # for line in lines:
    #     print(line.strip())

    # print(bot_response)

    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": chat_responses})


@app.get("/image", response_class=HTMLResponse)
async def image_page(request: Request):
    return templates.TemplateResponse("image.html", {"request": request})

@app.post("/image", response_class=HTMLResponse)
async def create_image(request: Request, user_input: Annotated[str, Form()]):

    response = openai.images.generate(
        model="dall-e-3",
        prompt=user_input,
        n=1,
        size="1024x1024", # size="512x512" not allowed in dall-e-3

    )

    image_url = response.data[0].url
    return templates.TemplateResponse("image.html", {"request": request, "image_url": image_url})