"""
Serviço de cálculo do estado emocional de um pet.

Lógica pura — sem banco de dados, sem IA.
Recebe os valores dos registros de comportamento e retorna o estado emocional.

Estados possíveis (usados pelo frontend para escolher a animação):
- "animado"    — todos os campos >= 4
- "agitado"    — agitacao >= 4
- "triste"     — humor <= 2 e agitacao <= 2
- "sonolento"  — sono <= 2
- "com_fome"   — apetite <= 2
- "feliz"      — demais casos (humor >= 4 e agitacao <= 3)
"""


def calcular_estado_emocional(
    agitacao: int,
    sono: int,
    apetite: int,
    humor: int,
) -> str:
    """Calcula o estado emocional com base nos registros de comportamento."""
    if agitacao >= 4 and sono >= 4 and apetite >= 4 and humor >= 4:
        return "animado"
    if agitacao >= 4:
        return "agitado"
    if humor <= 2 and agitacao <= 2:
        return "triste"
    if sono <= 2:
        return "sonolento"
    if apetite <= 2:
        return "com_fome"
    return "feliz"
