from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from gerar_df import gerar_df_atendimentos

app = FastAPI()

# Permitir acesso externo (como do Bubble)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # depois você pode restringir ao domínio do Bubble
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def raiz():
    return {"mensagem": "API funcionando"}

@app.get("/dados")
def dados(email: str = Query(...)):
    df = gerar_df_atendimentos()
    if df.empty:
        return {"dados": []}
    if "email" in df.columns:
        df = df[df["email"] == email]
    return df.to_dict(orient="records")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
