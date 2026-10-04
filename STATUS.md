# Status (2026-10-03 23:00 → 2026-10-04, atualizado depois que você acordou)

Resumo do que foi feito, o que falta, e exatamente o que preciso de você.

**Atualização do dia:** você pediu as "demais funcionalidades" e priorizou sync real
com Supabase. Feito — não é mais schema parado, é sync de verdade rodando contra o
projeto `hacknation` real, confirmado consultando a tabela direto. Detalhes na seção
atualizada abaixo.

## O que está pronto e testado

**Pipeline de ML (`model/`)** — completo, 34 testes passando (`pytest tests/`).
Os 3 modelos foram treinados de verdade nos datasets oficiais do desafio:

| Cultura | Dataset | Imagens treino | Acurácia 5-fold | Acurácia balanceada | Teste (held-out) |
|---|---|---|---|---|---|
| Café (BRACOL) | Mendeley | 940 | 81.7% | 76.8% | 79.9% |
| Mandioca (Makerere) | Kaggle | 14.977 | 72.0% | 56.8% | 72.4% |
| Feijão (iBean) | Kaggle | 693 | 91.3% | 91.3% | 91.2% |

Detalhes completos, incluindo por-fonte, em `model/artifacts/model_registry.json`.
A mandioca tem acurácia mais baixa — é esperado e já documentado (classes desbalanceadas
~12x), não é bug.

**App React Native (`app/`)** — roda de ponta a ponta no Simulador iOS (iPhone 17 Pro).
Verificado com screenshots reais em `docs/screenshots/`:
- Seleção de cultura (café/mandioca/feijão)
- Captura de foto → pré-processamento (Skia) → inferência TFLite on-device →
  cabeça SVM → resultado com confiança
- Guardrail de confiança implementado (abaixo do limiar = "not sure, ask a person")
- Persistência local em SQLite confirmada (contador de observações incrementou
  corretamente entre reinícios do app)
- **Sync real com Supabase** — cada observação salva localmente é enviada pro projeto
  `hacknation` (chbhhzypwvkqmojvtcmx) quando há conexão. Confirmado de verdade:
  classifiquei uma foto no app e consultei a tabela `observations` no Supabase e a
  linha estava lá. Schema aplicado com RLS habilitado e políticas corretas.
  Achei e corrigi um bug sutil do Postgres no caminho: `ON CONFLICT` (usado no
  upsert) exige política de SELECT, não só INSERT/UPDATE — sem isso toda tentativa
  de sync falhava com um erro que parecia ser de permissão de escrita mas não era.
  Documentado em `supabase/schema.sql`.
- 13 testes JS passando (`cd app && npx jest`) — incluindo testes novos da lógica
  de sync (sucesso, falha, offline, nada pendente)

**Documentação**: `ARCHITECTURE.md` e `PITCH_SCRIPT.md` atualizados e batendo com o
que foi de fato implementado (não é mais só plano, é o que existe).

## O que falta — e o que eu preciso de você

1. **Testar no seu celular de verdade (ou no simulador, interagindo você mesmo)**
   — eu não consegui interagir com a tela do simulador durante a madrugada porque
   o painel do Simulador iOS do Claude Code pede uma autorização sua de "Let Claude
   use it", que só aparece na interface — não dá pra aprovar programaticamente.
   Tudo que validei foi via screenshot (`xcrun simctl io screenshot`), sem tocar na tela.
   **Ação sua:** abra o app (`cd app && npx react-native run-ios`) e toque em
   "Pick a leaf photo" com uma foto real seguidora da galeria — isso eu não testei.
   Se não tiver uma folha à mão, o botão "Try a sample photo instead" já roda o
   pipeline real com uma foto de treino de verdade (não é mockado).

2. ~~Supabase~~ — **feito**. Aplicado de verdade no projeto real via MCP, sync
   funcionando ponta a ponta. Fotos em si NÃO são enviadas (só os dados da
   observação) — decisão deliberada de escopo, não esquecimento.

3. **Android** — não configurei (sem Android Studio instalado). Só validei iOS.

4. **Ainda faltam** (perguntei a você hoje, você priorizou sync primeiro):
   - Áudio em idioma local (hoje só tem texto em inglês)
   - Captura de GPS na observação (campo já existe no schema, não é preenchido)
   - Dashboard do extensionista/cooperativa (não existe nem protótipo)

5. **BRACOL (café) teve um problema real**: o zip da Mendeley está corrompido
   (sem diretório central válido — não é erro meu, é o arquivo deles mesmo).
   Escrevi um script de recuperação manual (`model/scripts/recover_bracol_zip.py`)
   que recuperou 1402 das 1747 imagens (80%). Documentado em `model/README.md`.
   Se quiser tentar de novo no futuro, talvez a Mendeley já tenha corrigido o arquivo.

## Pastas novas

```
small-ai-bean-hackathon/
├── ARCHITECTURE.md, PITCH_SCRIPT.md   (atualizados)
├── STATUS.md                          (este arquivo)
├── docs/screenshots/                  (4 capturas reais do app funcionando)
├── model/                             (pipeline Python, testado, 3 modelos treinados)
│   ├── README.md                      (detalhes técnicos + issues conhecidos)
│   ├── leafscout_ml/                  (pacote testável)
│   ├── artifacts/                     (backbone.tflite + 3 heads .json + registry)
│   └── tests/                         (34 testes)
├── app/                               (React Native, iOS verificado)
│   ├── README.md
│   ├── src/
│   └── __mocks__/                     (mocks dos módulos nativos p/ os testes Jest)
└── supabase/schema.sql                (aplicado de verdade no projeto real)
```

Pode gravar o vídeo com o que está aí. Qualquer coisa, só rodar `npx react-native
run-ios` de novo que o app sobe limpo (0 observações, café selecionado por padrão).
