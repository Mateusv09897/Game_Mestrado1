# Pesquisadoras em Jogo

Jogo educativo em Pygame para a SNCT/IFAM. Cada estudante escolhe uma pesquisadora e vive uma missão curta de exploração no campus ilustrado.

As fases têm até **3 minutos**, movimentação, pontos interativos e uma pergunta final. As missões apresentam Lucilene (Botânica), Deuzilene (educação, arte e tecnologia), Ana Cláudia (memória e formação) e Francisca (linguagem, extensão e equidade).

## Executar

Requer Python 3.10+.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate

python -m pip install -r requirements.txt
python main.py
```

## Controles

| Ação | Tecla |
| --- | --- |
| Escolher pesquisadora | `←` `→` ou `1` a `4` |
| Iniciar / confirmar | `Enter` |
| Movimentar personagem | `WASD` ou setas |
| Interagir com uma pista | `E` |
| Responder desafio | `1`, `2` ou `3` |
| Voltar ao menu | `Esc` |
| Tela cheia | `F11` |

Os sprites são os arquivos aprovados e disponibilizados pela equipe na pasta do projeto. Cenário e interface são originais.