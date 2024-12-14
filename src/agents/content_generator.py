import os
from typing import Dict, List

from dotenv import load_dotenv
from openai import OpenAI

# Forçar recarregamento das variáveis de ambiente
load_dotenv(override=True)


class ContentGenerator:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("API key não configurada corretamente no arquivo .env")

        # Inicialização simplificada do cliente
        self.client = OpenAI()

        # Definições de personas
        self.personas = {
            "adultos": {
                "description": "Adultos acima de 18 anos",
                "tone": "profissional e informativo",
                "vocabulary": "maduro e técnico quando necessário",
                "interests": "carreira, finanças, bem-estar, família",
            },
            "adolescentes": {
                "description": "Jovens de 13 a 18 anos",
                "tone": "descontraído e atual",
                "vocabulary": "jovem e com gírias moderadas",
                "interests": "estudos, música, tecnologia, amizades",
            },
            "criancas": {
                "description": "Crianças até 12 anos",
                "tone": "divertido e educativo",
                "vocabulary": "simples e lúdico",
                "interests": "diversão, aprendizado, jogos, família",
            },
        }

    def _enhance_image_prompt(self, base_prompt: str, style: str = "modern") -> str:
        """Melhora o prompt para geração de imagens mais realistas."""

        # Detectar estação do ano e contexto temporal
        seasons_keywords = {
            "verão": ["praia", "sol", "calor", "férias", "sorvete", "piscina"],
            "outono": ["folhas secas", "outono", "clima ameno", "tons terrosos"],
            "inverno": ["frio", "neve", "natal", "aconchego", "casaco"],
            "primavera": ["flores", "jardim", "colorido", "renovação"],
        }

        # Identificar estação do ano baseado no prompt
        detected_season = None
        for season, keywords in seasons_keywords.items():
            if any(keyword.lower() in base_prompt.lower() for keyword in keywords):
                detected_season = season
                break

        # Configurações de fotografia profissional
        photography_settings = {
            "modern": f"""
                Professional DSLR photography,
                Natural daylight,
                Shallow depth of field,
                Rule of thirds composition,
                Real world location,
                {f'Authentic {detected_season} scene' if detected_season else 'Authentic environment'}
            """,
            "corporate": f"""
                Professional studio photography,
                Soft studio lighting setup,
                Clean minimalist background,
                Commercial photography style,
                Professional environment,
                {f'Seasonal elements of {detected_season}' if detected_season else 'Timeless setting'}
            """,
            "casual": f"""
                Lifestyle photography,
                Natural available light,
                Environmental context,
                Documentary style,
                Real location setting,
                {f'Natural {detected_season} environment' if detected_season else 'Natural setting'}
            """,
        }

        # Aspectos sazonais específicos
        seasonal_lighting = {
            "verão": "bright natural sunlight, golden hour warmth, clear sky lighting",
            "outono": "soft diffused daylight, warm golden tones, afternoon sun",
            "inverno": "cool natural light, overcast illumination, morning frost lighting",
            "primavera": "soft morning light, natural diffusion, fresh daylight",
        }

        # Elementos técnicos focados em realismo
        technical_specs = [
            "photojournalistic style",
            "unedited photograph",
            "raw camera output",
            "authentic scene",
            "real world lighting",
            "natural color grading",
            "no digital effects",
            "no post-processing",
            "no artificial elements",
        ]

        # Aspectos a evitar
        avoid_elements = """
            Avoid completely:
            - Digital art elements
            - CGI or 3D rendering
            - Artificial textures
            - Unrealistic colors
            - Perfect symmetry
            - Stock photo look
            - Artificial poses
            - Human elements
            - Overprocessed effects
            - Instagram filters
            - HDR effects
        """

        # Construir o prompt final
        style_guide = photography_settings.get(style, photography_settings["modern"])
        lighting = seasonal_lighting.get(detected_season, "natural available light")

        prompt = f"""
            Create an authentic, unedited photograph:

            Main Subject: {base_prompt}

            Photography Approach:
            {style_guide}
            
            Technical Requirements:
            - Camera: Full-frame DSLR
            - Lens: Prime lens, natural perspective
            - Lighting: {lighting}
            - Focus: Sharp main subject
            - Composition: Professional photographic principles
            
            Key Aspects:
            {', '.join(technical_specs)}
            
            {avoid_elements}

            Critical Notes:
            - Must look like a real photograph
            - No digital manipulation
            - No human elements
            - Natural imperfections allowed
            - Authentic {detected_season if detected_season else 'temporal'} context
        """

        return prompt.strip()

    async def generate_content_for_personas(
        self,
        topic: str,
        tone: str,
        content_type: str,
        personas: List[str] = ["adultos", "adolescentes", "criancas"],
    ) -> List[Dict]:
        """Gera conteúdo adaptado para diferentes personas."""
        results = []

        for persona in personas:
            if persona not in self.personas:
                continue

            persona_info = self.personas[persona]
            try:
                # Gerar texto do post adaptado para a persona
                completion = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": f"""Crie um post para redes sociais sobre {topic}.

Público-alvo: {persona_info['description']}
Requisitos:
- Tom de voz: {tone}, adaptado para {persona_info['tone']}
- Tipo de conteúdo: {content_type}
- Vocabulário: {persona_info['vocabulary']}
- Interesses: {persona_info['interests']}
- Texto com no máximo 280 caracteres
- 5 hashtags relevantes (sem anos)
- Descrição da cena para foto (sem pessoas)

Responda EXATAMENTE neste formato:
POST: [texto do post]
HASHTAGS: [hashtag1] [hashtag2] [hashtag3] [hashtag4] [hashtag5]
IMAGEM_PROMPT: [descrição da cena sem pessoas]""",
                        }
                    ],
                )

                # Processar a resposta
                response_text = completion.choices[0].message.content
                parts = {}

                # Extrair cada seção com tratamento de erro
                for line in response_text.split("\n"):
                    if ": " in line:
                        key, value = line.split(": ", 1)
                        parts[key.strip()] = value.strip()

                # Verificar se temos todas as partes necessárias
                if (
                    not parts.get("POST")
                    or not parts.get("HASHTAGS")
                    or not parts.get("IMAGEM_PROMPT")
                ):
                    raise ValueError(
                        f"Resposta incompleta do modelo para persona {persona}"
                    )

                # Melhorar o prompt da imagem e gerar
                image_style = {
                    "educativo": "modern",
                    "promocional": "corporate",
                    "engajamento": "casual",
                }.get(content_type, "modern")

                enhanced_image_prompt = self._enhance_image_prompt(
                    f"{topic}. {parts.get('IMAGEM_PROMPT')}", image_style
                )

                image_response = self.client.images.generate(
                    model="dall-e-3",
                    prompt=enhanced_image_prompt,
                    size="1024x1024",
                    quality="hd",
                    n=1,
                    style="natural",
                )

                results.append(
                    {
                        "persona": persona,
                        "post_text": parts.get("POST", ""),
                        "hashtags": parts.get("HASHTAGS", ""),
                        "image_url": image_response.data[0].url,
                        "image_prompt": enhanced_image_prompt,  # Para debug
                    }
                )

            except Exception as e:
                print(f"Erro ao gerar conteúdo para persona {persona}: {str(e)}")
                continue

        return results

    # Manter o método generate_content existente para compatibilidade
    async def generate_content(self, topic: str, tone: str, content_type: str) -> Dict:
        """Gera conteúdo para uma única versão (mantido para compatibilidade)."""
        results = await self.generate_content_for_personas(
            topic, tone, content_type, personas=["adultos"]
        )
        return results[0] if results else {}
