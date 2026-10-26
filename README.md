# Extrator de Dados Estruturados

API em Python que transforma texto não estruturado — e-mails, currículos e notas fiscais — em JSON validado por schemas Pydantic. A inferência é feita pela API da Anthropic; nenhum modelo local pesado é necessário.

> **Status do deploy:** o projeto inclui configuração pronta para Render, mas ainda não tem uma URL pública. Para publicar, conecte este repositório a uma conta Render, configure `ANTHROPIC_API_KEY` como secret e use o Blueprint `render.yaml`. Não há credenciais ou repositório remoto disponíveis neste ambiente para concluir e verificar o deploy. Depois da publicação, substitua o link abaixo pela URL real.

**Versão online:** [ainda não publicada — instruções de deploy abaixo](#deploy-no-render)

## O problema

Informações úteis chegam em formatos imprevisíveis. A API recebe o texto e um tipo de documento indicado pelo cliente, pede ao modelo somente os campos do schema correspondente, valida a resposta e persiste o resultado estruturado. Campos ausentes não devem ser inventados.

## Arquitetura

```text
Cliente → FastAPI (/v1/extractions) → ExtractionService → Anthropic API
                         │                    │
                         │                    └→ Pydantic (schema por tipo + retry)
                         └→ Repository / SQLAlchemy → PostgreSQL ou SQLite
```

- `app/api`: contrato HTTP e validação básica da entrada.
- `app/services`: chamada à Anthropic, parsing JSON e validação/retry.
- `app/schemas`: modelos estritos para `email`, `resume` e `invoice`.
- `app/repositories`: persistência SQLAlchemy. A API guarda somente o JSON extraído, não o texto bruto.
- `examples/documents.json`: três exemplos realistas por tipo, cada um com saída esperada.
- `docs/demo.svg`: demonstração visual estática de entrada bagunçada e saída validada.

## Rodar localmente

Requer Python 3.11+ e uma chave da API Anthropic. SQLite é usado por padrão, sem instalação adicional.

1. Crie e ative um ambiente virtual:

   ```bash
   python -m venv .venv
   # macOS/Linux
   source .venv/bin/activate
   # Windows PowerShell: .venv\Scripts\Activate.ps1
   ```

2. Instale as dependências e configure o ambiente:

   ```bash
   pip install -r requirements.txt
   cp .env.example .env
   ```

   No Windows, copie `.env.example` para `.env` manualmente. Edite `.env` e defina `ANTHROPIC_API_KEY` com uma chave válida. Nunca commit o `.env`.

3. Inicie a API:

   ```bash
   uvicorn app.main:app --reload
   ```

4. Abra <http://127.0.0.1:8000/docs> para testar interativamente. O health check está em <http://127.0.0.1:8000/health>.

Exemplo de chamada:

```bash
curl -X POST http://127.0.0.1:8000/v1/extractions \
  -H 'Content-Type: application/json' \
  -d '{"document_type":"email","text":"De: Ana <ana@example.com>\nAssunto: Reunião\nPode confirmar para amanhã?"}'
```

A resposta `201` inclui `id`, `document_type`, os campos extraídos em `data` e `created_at`. Tipos aceitos: `email`, `resume`, `invoice`. O limite padrão de entrada é 30.000 caracteres (`MAX_INPUT_CHARS`).

Para usar PostgreSQL, configure `DATABASE_URL`, por exemplo `postgresql://usuario:senha@host:5432/banco`. O adaptador converte a URL para psycopg 3. As tabelas são criadas na inicialização; para um produto com evolução de schema, adicione migrações Alembic.

## Testes

```bash
pytest -q
```

Os testes cobrem validação dos schemas, saída malformada e retry, endpoints principais, persistência, texto vazio e erro de saída. A API Anthropic é simulada: os testes não precisam de chave, rede ou créditos.

## Demonstração

Veja [`docs/demo.svg`](docs/demo.svg) (abrível no navegador) para um exemplo visual de e-mail desorganizado e JSON validado. A imagem é uma demonstração estática; gere uma captura real após iniciar a API abrindo `/docs`, enviando uma entrada de `examples/documents.json` e capturando a resposta. O serviço não inclui interface web própria.

## Deploy no Render

1. Faça push do projeto para um repositório Git e conecte-o ao Render.
2. Crie um **Blueprint** a partir do repositório; o Render lerá `render.yaml`, criando o serviço Docker e um PostgreSQL gerenciado.
3. Defina `ANTHROPIC_API_KEY` nos Environment Variables do serviço (secret, não sincronizado pelo YAML). Não coloque a chave no código ou no Git.
4. Aguarde o health check `/health` ficar saudável. Teste `POST /v1/extractions` usando a URL atribuída e uma chave Anthropic válida.
5. Atualize o link **Versão online** deste README com a URL pública do serviço.

O banco configurado no Blueprint tem custo conforme o plano disponível na conta Render. Confirme preços e limites atuais antes de provisionar. O serviço retorna `503` quando a chave não está configurada e `502` quando o modelo não produz saída válida.

## Decisões técnicas e trade-offs

- **Modelo/provedor:** Anthropic Claude Haiku (`claude-haiku-4-5-20251001`) via SDK oficial. É uma escolha de modelo pequeno para manter custo e latência inferiores aos de modelos maiores, sem executar inferência local. O alias pode mudar conforme disponibilidade na conta; `ANTHROPIC_MODEL` permite trocar o identificador. Não há fallback automático para outro provedor.
- **Validação:** o modelo recebe o JSON Schema gerado por Pydantic e retorna JSON. O resultado é parseado e validado localmente; em caso de JSON malformado ou schema incompatível, há uma segunda tentativa com o erro de validação. Falha após a tentativa adicional vira HTTP `502`, em vez de persistir dados inválidos. Essa abordagem mantém o fluxo simples, mas a validação estrutural não garante que os fatos extraídos sejam verdadeiros.
- **Custo e latência:** cada extração normalmente usa uma chamada; falha de validação pode dobrar chamadas, custo e latência. O limite de texto controla entradas acidentais muito grandes, mas não substitui rate limiting nem quotas por usuário. O projeto não estima preços porque tarifas e contexto variam por modelo/conta.
- **Dados sensíveis:** documentos podem conter dados pessoais. O texto é enviado à Anthropic para inferência; avalie os termos, a região e os controles de retenção aplicáveis antes de usar dados reais. O texto bruto não é persistido nem incluído nos logs; somente os campos extraídos são salvos. A API de demonstração não tem autenticação, autorização, exclusão ou política de retenção. Não a exponha a dados sensíveis sem implementar esses controles.
- **Persistência:** PostgreSQL em produção e SQLite para desenvolvimento. Vetores não foram incluídos: busca semântica não é necessária para o escopo de extração e adicionaria custo e operação.
- **Datas e valores:** schemas usam datas ISO e `Decimal` para valores monetários. Datas incompletas e moedas ambíguas podem resultar em `null`; a interpretação do modelo ainda precisa de revisão em fluxos financeiros ou regulados.

## Limitações

- O tipo do documento é escolhido pelo cliente; não há classificação automática.
- Não há OCR, upload de arquivos, autenticação, rate limiting, observabilidade avançada ou revisão humana integrada.
- A extração é probabilística: saída validada pode estar semanticamente errada. Para produção, inclua avaliação com corpus representativo e revisão adequada ao risco.
- `create_all` serve para este exemplo; mudanças de schema em serviço persistente devem usar migrações.
