from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from gerar_df import gerar_df_atendimentos
import os

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
    return df.fillna("").to_dict(orient="records")

@app.get("/baixar-relacao")
def baixar_relacao(email: str = Query(...)):
    df = gerar_df_atendimentos()
    if df.empty:
        return {"erro": "Nenhum dado disponível"}

    if "email" in df.columns:
        df = df[df["email"] == email]

    if df.empty:
        return {"erro": "Nenhum dado encontrado para este e-mail"}

    nome_arquivo = "Relacao_de_Atendimentos.xlsx"
    caminho_arquivo = f"/tmp/{nome_arquivo}"

    df.to_excel(caminho_arquivo, index=False, engine='openpyxl')

    return FileResponse(
        path=caminho_arquivo,
        # filename=nome_arquivo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
