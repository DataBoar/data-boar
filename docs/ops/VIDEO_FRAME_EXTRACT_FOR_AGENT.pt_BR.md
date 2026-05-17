# Extração de frames de vídeo para contexto do assistente (Windows, token-aware)

**English:** [VIDEO_FRAME_EXTRACT_FOR_AGENT.md](VIDEO_FRAME_EXTRACT_FOR_AGENT.md)

## Finalidade

Modelos em chat **não decodificam vídeo** de forma confiável como um humano a ver um *stream*. Na **estação Windows do operador**, o assistente deve usar uma **escada estruturada**: metadados primeiro, depois **PNG esparsos** em **instantes nomeados** (ou lista CSV curta). Espelha o padrão do repo com **`es-find.ps1`** (caminho rápido + instalação documentada) em vez de varrer o disco ou o tempo sem teto.

## Taxonomia (complexidade vs tokens)

| Nível | O quê | Quando |
| ----- | ---- | ------ |
| **L0** | Nada com o arquivo de mídia | Vídeo enorme, irrelevante, ou o operador cola texto/screenshot. |
| **L1** | Só **`ffprobe`**: duração, *codecs*, resolução | Decidir quantas amostras; detetar só áudio. |
| **L2** | **`video-frame-samples.ps1`**: poucos PNG nos **segundos** indicados (ex.: “~3s mostra o erro”) | Padrão para clipes Maestro / terminal / prova de UI. |
| **L3** | Amostragem densa (ex.: ffmpeg `fps=1` no vídeo inteiro) | Só quando não há **nenhum** *timestamp* útil; custo alto em tokens de imagem. |

## Automação principal

**Script:** **`scripts/video-frame-samples.ps1`**

**Instalação (PC do operador):** `winget install ffmpeg` (coloca **`ffmpeg`** / **`ffprobe`** no PATH; o script também procura WinGet Links).

**Exemplos:**

```powershell
# Só duração
.\scripts\video-frame-samples.ps1 -MediaPath "D:\Captures\clip.mp4" -ProbeOnly

# Dica do operador: conteúdo perto de 3s e 12s
.\scripts\video-frame-samples.ps1 -MediaPath "D:\Captures\clip.mp4" -Timestamp 3 -Timestamp 12

# Lista separada por vírgulas
.\scripts\video-frame-samples.ps1 -MediaPath "D:\Captures\clip.mp4" -TimestampsCsv "0,3,10.5"

# Reduz largura para payloads de visão menores (largura máxima 1280px)
.\scripts\video-frame-samples.ps1 -MediaPath "D:\Captures\clip.mp4" -Timestamp 3 -MaxWidth 1280
```

A saída imprime **`output_dir`** e uma linha por caminho **PNG**; o assistente usa **`read_file`** nessas imagens (mesmo fluxo que *screenshot*).

## Contrato com o operador

1. Preferir **segundos** (“~3s”, “em 0:12”) para o assistente rodar **L2** sem varrer o *clip* inteiro.
2. Se o caminho tiver espaços ou unicode, usar aspas; o script usa **`-LiteralPath`** onde importa.
3. Se faltar **`ffmpeg`**, o script sai com código **3** e **uma linha** a sugerir `winget` — a mesma honestidade que **`es-find`** quando **`es.exe`** falta.

## Ferramentas opcionais (não obrigatórias)

| Ferramenta | Papel |
| ---------- | ----- |
| **ffmpeg** | Necessário para este fluxo; procura, codifica e posiciona no tempo. |
| **whisper / STT local** | Transcrição de fala — orçamento de tokens à parte; só se a tarefa for diálogo pesado. |

Não precisa de um segundo “Everything de vídeo”: **descoberta de caminho** continua **`es-find.ps1`**; **extração no tempo** fica **`video-frame-samples.ps1`**.

## Referências

- **`docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md`** (linha no hub)
- **`docs/ops/WINDOWS_FAST_CLI_WRAPPERS.md`**
- **`.cursor/skills/video-frames-for-agent/SKILL.md`**
- **`.cursor/rules/repo-scripts-wrapper-ritual.mdc`**
