# Origon Studio AI

Studio pessoal para transformar produtos, links e mídias em variações de vídeos verticais para Shopee Video, Reels, TikTok e Shorts.

## O que esta entrega contém

- Dashboard, produtos, projetos, lotes, histórico, lixeira, configurações e diagnóstico.
- Persistência SQLite e armazenamento local organizado.
- Importação assistida por URL com revisão obrigatória.
- AI Director local baseado em regras, Claim Guard e Creative Matrix.
- 1, 3 ou 5 estratégias/roteiros por produto.
- Fila de lotes para até 5 produtos.
- Provider Hub com fallback local; conectores externos começam desativados.
- Diagnóstico de FFmpeg, FFprobe, Piper, WebGPU/configuração e espaço em disco.
- Exportação de pacote editorial: título, legenda, hashtags, palavras-chave e comentário fixado.
- Render demonstrativo com FFmpeg quando há mídias locais válidas.

## Instalação no Codespaces

```bash
chmod +x setup-origon.sh start-origon.sh diagnose-origon.sh repair-origon.sh update-origon.sh
./setup-origon.sh
./start-origon.sh
```

Abra a porta 3000. A API e a documentação ficam na porta 8000 (`/docs`).

## Windows

Use o WSL2 nesta versão. O script `scripts/setup-windows-wsl.sh` documenta o caminho. Um instalador nativo é uma evolução posterior.

## Limitações honestas

- A importação de URL é assistida e depende do conteúdo público acessível; não burla login, anti-bot ou restrições da Shopee.
- Serviços gratuitos externos podem ter filas e cotas. O fluxo nunca depende deles.
- WebLLM e ComfyUI são conectores opcionais. O motor de regras local funciona sem GPU.
- Publicação automática na Shopee não está habilitada sem credenciais e aprovação oficiais.

Consulte `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE.md` e `docs/PROVIDERS.md`.

## Novidades v0.2

- Biblioteca persistente de imagens e vídeos por produto.
- FFprobe: resolução, duração e presença de áudio.
- Favoritos e bloqueio de mídia.
- Media Director automático e associação manual por cena.
- Editor vertical por versão.
- Render MP4 720×1280 com FFmpeg e textos.
- Quality Gate básico.
- Download do vídeo e pacote editorial ZIP.

### Migração da v0.1

Extraia este pacote sobre o repositório atual. O banco SQLite é preservado e as novas tabelas são criadas automaticamente ao iniciar.
