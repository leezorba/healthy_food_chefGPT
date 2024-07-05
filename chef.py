from fastapi import FastAPI, Form, Request, Body
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import Pinecone

embeddings = OpenAIEmbeddings()

vectorstore = Pinecone.from_existing_index(
    "recipes",
    embeddings,
)

app = FastAPI(
    title="ChefGPT - Your Best Korean Cuisine Recipe Companion",
    description="ChefGPT is your culinary companion for Korean cuisine! Simply input an ingredient, and ChefGPT will provide you with a variety of delicious Korean recipes featuring that ingredient. Discover new dishes and enhance your cooking skills with tailored suggestions from ChefGPT.",
    servers=[
        {"url": "https://supplemental-slip-divx-valium.trycloudflare.com"},
    ],
)

user_token_db = {}


class Document(BaseModel):
    page_content: str = Field(
        description="detailed recipe, provides a source link if one is available."
    )


@app.get(
    "/recipes",
    summary="Returns a list of recipes.",
    description="Given an ingredient, this endpoint returns a curated list of recipes that include that ingredient, helping you explore new culinary possibilities.",
    response_description="A list of Document objects, each containing detailed recipes and preparation instructions, tailored to the specified ingredient.",
    response_model=list[Document],
    openapi_extra={
        "x-openai-isConsequential": False,
    },
)
def get_recipe(ingredient: str):
    docs = vectorstore.similarity_search(ingredient)
    return docs


@app.get(
    "/add_favorite",
    summary="Adds a recipe to the user's favorite recipe list.",
    description="Receives a name of the recipe and add it to the user's favorite recipe list.",
)
def add_favorite_recipe(request: Request, name: str):
    print(request.headers)
    token = request.headers["authorization"].split()[1]
    if token not in user_token_db:
        user_token_db[token] = {"favorite_food_list": []}
    user_token_db[token]["favorite_food_list"].append(name)
    return {"ok": True}


@app.get(
    "/get_favorite",
    summary="Receives the user's favorite food list.",
    description="Receives the user's favorite food list.",
    response_description="User's favorite food list",
    response_model=list[str],
)
def get_favorite_recipe(request: Request):
    token = request.headers["authorization"].split()[1]
    if token not in user_token_db:
        return []
    else:
        return user_token_db[token]["favorite_food_list"]


@app.get(
    "/authorize",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def handle_authorization(client_id: str, redirect_uri: str, state: str):
    user_token_db[client_id] = {"favorite_food_list": []}
    return f"""
    <html>
        <head>
            <title>ChefGPT Login</title>
        </head>
        <body>
            <h1>Log Into ChefGPT</h1>
            <a href="{redirect_uri}?code=ABCDEF&state={state}">Authorize ChefGPT</a>
        </body>
    </html>
    """


@app.post(
    "/token",
    include_in_schema=False,
)
def handle_token(code=Form(...)):
    return {"access_token": code}
