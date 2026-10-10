# Pesquisadoras em Ação

Jogo educativo em Pygame para a SNCT/IFAM. Cada estudante escolhe uma pesquisadora e vive uma missão curta de exploração no Campus Manaus Centro ilustrado em pixel art.

As fases têm até **3 minutos**, movimentação, pontos interativos e uma pergunta final. As missões apresentam Lucilene (Botânica), Deuzilene (educação, arte e tecnologia), Ana Cláudia (memória e formação) e Francisca (linguagem, extensão e equidade).

## Executar

Requer Python 3.10+.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows
.venv\\Scripts\\activate

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

## Estrutura de uma missão

1. Caminhe pelo cenário e aproxime-se dos objetos brilhantes.
2. Aperte `E` para investigar cada pista.
3. Depois de recolher todas, aperte `E` para abrir o minidesafio da pesquisadora.
4. Conclua a associação de pistas (ou a sequência de ritmo e código da Deuzilene).
5. Responda ao desafio final para marcar a missão como concluída.

## Trilha sonora

A trilha instrumental do projeto já está incluída em `assets/music/trilha.ogg` e é tocada automaticamente em loop, com volume moderado. Para substituí-la no futuro, mantenha o nome `trilha.ogg` (formato recomendado); `trilha.mp3` ou `trilha.wav` também funcionam.

## Créditos e uso dos assets

Os sprites de cada pesquisadora são os arquivos aprovados e disponibilizados pela equipe na pasta do projeto. O cenário e a interface são originais; o jogo não reproduz assets, personagens ou interface de outros jogos.
