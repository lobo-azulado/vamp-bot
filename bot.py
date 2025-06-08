import discord
from discord.ext import commands
from discord import app_commands
import random

# Configuração do bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

class VampireDiceResult:
    def __init__(self, dice_count, difficulty, hunger, results, hunger_dice_results, title=None):
        self.dice_count = dice_count
        self.difficulty = difficulty
        self.hunger = hunger
        self.results = results
        self.hunger_dice_results = hunger_dice_results
        self.title = title
        
        # Calcular sucessos brutos
        # 6-9 = 1 sucesso cada, 10 = 2 sucessos cada
        regular_successes = sum(1 for roll in results if 6 <= roll <= 9)
        critical_successes = sum(2 for roll in results if roll == 10)
        raw_successes = regular_successes + critical_successes
        
        # Calcular 1s em toda a parada (reduzem sucessos)
        total_ones = sum(1 for roll in results if roll == 1)
        
        # Sucessos finais = sucessos brutos - 1s
        self.regular_successes = regular_successes
        self.critical_successes = critical_successes // 2  # Quantidade de 10s
        self.raw_successes = raw_successes
        self.total_ones = total_ones
        self.successes = max(0, raw_successes - total_ones)
        
        # Verificar se atingiu a dificuldade
        self.success = self.successes >= difficulty
        
        # Verificar falha bestial
        self.bestial_failure = False
        if not self.success and hunger > 0:
            self.bestial_failure = any(roll == 1 for roll in hunger_dice_results)
        
        # Verificar sucesso bestial  
        self.bestial_success = False
        if not self.success and hunger > 0:
            self.bestial_success = any(roll == 10 for roll in hunger_dice_results)

def roll_vampire_dice(dice_count, difficulty, hunger, title=None):
    """Rola os dados seguindo as regras de Vampiro: A Máscara 5ª ed"""
    
    # Validações
    if dice_count <= 0:
        raise ValueError("Número de dados deve ser maior que 0")
    if difficulty <= 0:
        raise ValueError("Dificuldade deve ser maior que 0")
    if hunger < 0 or hunger > 5:
        raise ValueError("Nível de fome deve estar entre 0 e 5")
    if hunger > dice_count:
        raise ValueError("Nível de fome não pode ser maior que o número de dados")
    
    # Rolar todos os dados
    all_results = [random.randint(1, 10) for _ in range(dice_count)]
    
    # Separar dados de fome (primeiros X dados)
    hunger_dice = all_results[:hunger] if hunger > 0 else []
    
    return VampireDiceResult(dice_count, difficulty, hunger, all_results, hunger_dice, title)

# Modal para definir título
class TitleModal(discord.ui.Modal, title='📝 Definir Título da Rolagem'):
    def __init__(self, view):
        super().__init__()
        self.view = view

    title_input = discord.ui.TextInput(
        label='Título da Rolagem',
        placeholder='Ex: Teste de Persuasão, Ataque com Garras, Resistência...',
        default='',
        required=False,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        title_text = self.title_input.value.strip()
        self.view.title = title_text if title_text else None
        embed = self.view.create_embed()
        await interaction.response.edit_message(embed=embed, view=self.view)

def format_dice_results(result):
    """Formata os resultados dos dados para exibição"""
    
    # Criar representação visual dos dados
    dice_display = []
    for i, roll in enumerate(result.results):
        if i < result.hunger:
            # Dados de fome - usar emojis diferentes
            if roll == 1:
                dice_display.append(f"🩸**{roll}**")  # Falha bestial
            elif roll == 10:
                dice_display.append(f"🔥**{roll}**")  # Sucesso bestial potencial (2 sucessos)
            elif roll >= 6:
                dice_display.append(f"🩸✅`{roll}`")  # Sucesso de fome
            else:
                dice_display.append(f"🩸❌{roll}")  # Falha de fome
        else:
            # Dados normais
            if roll == 1:
                dice_display.append(f"💀**{roll}**")  # Falha crítica (reduz sucesso)
            elif roll == 10:
                dice_display.append(f"⭐**{roll}**")  # Sucesso crítico (2 sucessos)
            elif roll >= 6:
                dice_display.append(f"✅`{roll}`")  # Sucesso normal
            else:
                dice_display.append(f"❌{roll}")  # Falha normal
    
    return " ".join(dice_display)

# Modal para entrada de valores
class DiceRollModal(discord.ui.Modal, title='🎲 Configurar Rolagem de Dados'):
    def __init__(self):
        super().__init__()

    title_input = discord.ui.TextInput(
        label='Título da Rolagem (Opcional)',
        placeholder='Ex: Teste de Persuasão, Ataque com Garras, etc.',
        default='',
        required=False,
        max_length=50
    )

    dice_count = discord.ui.TextInput(
        label='Número de Dados',
        placeholder='Digite o número de dados (1-20)',
        default='5',
        min_length=1,
        max_length=2
    )
    
    difficulty = discord.ui.TextInput(
        label='Dificuldade',
        placeholder='Digite a dificuldade (1-10)',
        default='3',
        min_length=1,
        max_length=2
    )
    
    hunger = discord.ui.TextInput(
        label='Nível de Fome',
        placeholder='Digite o nível de fome (0-5)',
        default='0',
        min_length=1,
        max_length=1
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            dice = int(self.dice_count.value)
            diff = int(self.difficulty.value)
            hung = int(self.hunger.value)
            title = self.title_input.value.strip() if self.title_input.value.strip() else None
            
            # Validações
            if dice <= 0 or dice > 20:
                await interaction.response.send_message("❌ Número de dados deve estar entre 1 e 20", ephemeral=True)
                return
            
            if diff <= 0 or diff > 10:
                await interaction.response.send_message("❌ Dificuldade deve estar entre 1 e 10", ephemeral=True)
                return
                
            if hung < 0 or hung > 5:
                await interaction.response.send_message("❌ Nível de fome deve estar entre 0 e 5", ephemeral=True)
                return
                
            if hung > dice:
                await interaction.response.send_message("❌ Nível de fome não pode ser maior que o número de dados", ephemeral=True)
                return
            
            # Rolar os dados
            result = roll_vampire_dice(dice, diff, hung, title)
            embed = create_result_embed(result)
            await interaction.response.send_message(embed=embed)
            
        except ValueError:
            await interaction.response.send_message("❌ Por favor, digite apenas números válidos", ephemeral=True)

# View com botões interativos
class DiceConfigView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)  # 5 minutos de timeout
        self.dice_count = 5
        self.difficulty = 3
        self.hunger = 0
        self.title = None
    
    def create_embed(self):
        embed = discord.Embed(
            title="🎛️ Configurador de Dados - Vampiro V5",
            description="Use os botões abaixo para ajustar os valores e depois role os dados!",
            color=0x8B0000
        )
        
        # Mostrar título se definido
        if self.title:
            embed.add_field(
                name="📝 Título",
                value=f"**{self.title}**",
                inline=False
            )
        
        embed.add_field(
            name="🎲 Dados",
            value=f"**{self.dice_count}**",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Dificuldade", 
            value=f"**{self.difficulty}**",
            inline=True
        )
        
        embed.add_field(
            name="🩸 Fome",
            value=f"**{self.hunger}**",
            inline=True
        )
        
        embed.set_footer(text="💡 Clique nos botões para ajustar os valores")
        return embed

    # Botões para dados
    @discord.ui.button(label='Dados -', style=discord.ButtonStyle.red, row=0)
    async def dice_minus(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.dice_count > 1:
            self.dice_count -= 1
            # Ajustar fome se necessário
            if self.hunger > self.dice_count:
                self.hunger = self.dice_count
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label='Dados +', style=discord.ButtonStyle.green, row=0)
    async def dice_plus(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.dice_count < 20:
            self.dice_count += 1
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    # Botões para dificuldade
    @discord.ui.button(label='Dif -', style=discord.ButtonStyle.red, row=1)
    async def difficulty_minus(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.difficulty > 1:
            self.difficulty -= 1
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label='Dif +', style=discord.ButtonStyle.green, row=1)
    async def difficulty_plus(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.difficulty < 10:
            self.difficulty += 1
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    # Botões para fome
    @discord.ui.button(label='Fome -', style=discord.ButtonStyle.red, row=2)
    async def hunger_minus(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.hunger > 0:
            self.hunger -= 1
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label='Fome +', style=discord.ButtonStyle.green, row=2)
    async def hunger_plus(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.hunger < 5 and self.hunger < self.dice_count:
            self.hunger += 1
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    # Botão principal para rolar
    @discord.ui.button(label='🎲 ROLAR DADOS', style=discord.ButtonStyle.primary, row=3)
    async def roll_dice(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            result = roll_vampire_dice(self.dice_count, self.difficulty, self.hunger, self.title)
            embed = create_result_embed(result)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro: {str(e)}", ephemeral=True)

    # Botão para definir título
    @discord.ui.button(label='📝 Título', style=discord.ButtonStyle.secondary, row=3)
    async def set_title(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = TitleModal(self)
        await interaction.response.send_modal(modal)

    # Botão para abrir modal de entrada manual
    @discord.ui.button(label='✏️ Entrada Manual', style=discord.ButtonStyle.secondary, row=4)
    async def manual_input(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = DiceRollModal()
        await interaction.response.send_modal(modal)

    async def on_timeout(self):
        # Desabilitar todos os botões quando expirar
        for item in self.children:
            item.disabled = True

def create_result_embed(result):
    """Cria o embed com os resultados da rolagem"""
    
    # Título principal do embed
    main_title = "🎲 Resultado da Rolagem - Vampiro V5"
    if result.title:
        main_title = f"🎲 {result.title} - Vampiro V5"
    
    embed = discord.Embed(
        title=main_title,
        color=0x8B0000
    )
    
    # Adicionar informações da rolagem
    embed.add_field(
        name="📊 Parâmetros",
        value=f"**Dados:** {result.dice_count}\n**Dificuldade:** {result.difficulty}\n**Fome:** {result.hunger}",
        inline=True
    )
    
    # Mostrar resultados dos dados
    dice_display = format_dice_results(result)
    embed.add_field(
        name="🎯 Resultados dos Dados",
        value=dice_display,
        inline=False
    )
    
    # Mostrar sucessos com detalhamento completo
    success_text = f"**{result.successes}** de {result.difficulty} necessários\n"
    
    # Detalhamento dos sucessos
    details = []
    if result.regular_successes > 0:
        details.append(f"{result.regular_successes} sucessos normais")
    if result.critical_successes > 0:
        details.append(f"{result.critical_successes} críticos (×2)")
    if result.total_ones > 0:
        details.append(f"{result.total_ones} falhas críticas")
    
    if details:
        if result.total_ones > 0:
            success_text += f"*({' + '.join(details[:-1])} - {details[-1]} = {result.raw_successes} - {result.total_ones})*"
        else:
            success_text += f"*({' + '.join(details)} = {result.raw_successes})*"
    
    embed.add_field(
        name="✨ Sucessos",
        value=success_text,
        inline=True
    )
    
    # Determinar resultado final
    if result.bestial_failure:
        embed.add_field(
            name="🩸 FALHA BESTIAL",
            value="Falhou no teste e rolou 1 nos dados de fome!",
            inline=False
        )
        embed.color = 0x800000
    elif result.bestial_success:
        embed.add_field(
            name="🔥 SUCESSO BESTIAL",
            value="Falhou no teste mas rolou 10 nos dados de fome!",
            inline=False
        )
        embed.color = 0xFF4500
    elif result.success:
        embed.add_field(
            name="✅ SUCESSO",
            value="Teste bem-sucedido!",
            inline=False
        )
        embed.color = 0x228B22
    else:
        embed.add_field(
            name="❌ FALHA",
            value="Não atingiu o número necessário de sucessos",
            inline=False
        )
        embed.color = 0x696969
    
    # Adicionar legenda
    legend = "🩸 = Dado de Fome | ✅ = Sucesso | ❌ = Falha | 💀 = Falha Crítica | ⭐ = Sucesso Crítico (2 sucessos) | 🔥 = Potencial Bestial"
    embed.set_footer(text=legend)
    
    return embed

@bot.event
async def on_ready():
    print(f'{bot.user} está conectado e pronto!')
    print(f'Comandos disponíveis: /vamp, /dados, !vamp, !ajuda_vamp')
    
    # Sincronizar comandos slash
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos slash")
    except Exception as e:
        print(f"Falha ao sincronizar comandos: {e}")

# Comando slash principal com interface interativa
@bot.tree.command(name="dados", description="Abrir interface interativa para rolar dados de Vampiro V5")
async def interactive_dice(interaction: discord.Interaction):
    view = DiceConfigView()
    embed = view.create_embed()
    await interaction.response.send_message(embed=embed, view=view)

# Comando slash rápido
@bot.tree.command(name="vamp", description="Rolar dados de Vampiro V5 rapidamente")
@app_commands.describe(
    dados="Número de dados para rolar (1-20)",
    dificuldade="Número de sucessos necessários (1-10)",
    fome="Nível de fome (0-5)",
    titulo="Título personalizado para a rolagem (opcional)"
)
async def slash_vampire_roll(interaction: discord.Interaction, dados: int, dificuldade: int, fome: int = 0, titulo: str = None):
    try:
        # Validações
        if dados <= 0 or dados > 20:
            await interaction.response.send_message("❌ Número de dados deve estar entre 1 e 20", ephemeral=True)
            return
        
        if dificuldade <= 0 or dificuldade > 10:
            await interaction.response.send_message("❌ Dificuldade deve estar entre 1 e 10", ephemeral=True)
            return
            
        if fome < 0 or fome > 5:
            await interaction.response.send_message("❌ Nível de fome deve estar entre 0 e 5", ephemeral=True)
            return
            
        if fome > dados:
            await interaction.response.send_message("❌ Nível de fome não pode ser maior que o número de dados", ephemeral=True)
            return
        
        # Processar título
        title = titulo.strip() if titulo and titulo.strip() else None
        
        # Rolar os dados
        result = roll_vampire_dice(dados, dificuldade, fome, title)
        embed = create_result_embed(result)
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro: {str(e)}", ephemeral=True)

# Manter comandos antigos para compatibilidade
@bot.command(name='vamp', aliases=['vampiro', 'v5'])
async def roll_vampire(ctx, dados: int, dificuldade: int, fome: int = 0, *, titulo: str = None):
    """Comando de texto tradicional"""
    try:
        if dados <= 0 or dados > 20:
            await ctx.send("❌ Número de dados deve estar entre 1 e 20")
            return
        
        if dificuldade <= 0 or dificuldade > 10:
            await ctx.send("❌ Dificuldade deve estar entre 1 e 10")
            return
            
        if fome < 0 or fome > 5:
            await ctx.send("❌ Nível de fome deve estar entre 0 e 5")
            return
            
        if fome > dados:
            await ctx.send("❌ Nível de fome não pode ser maior que o número de dados")
            return
        
        # Processar título
        title = titulo.strip() if titulo and titulo.strip() else None
        
        result = roll_vampire_dice(dados, dificuldade, fome, title)
        embed = create_result_embed(result)
        await ctx.send(embed=embed)
        
    except ValueError as e:
        await ctx.send(f"❌ Erro: {str(e)}")
    except Exception as e:
        await ctx.send(f"❌ Erro inesperado: {str(e)}")

@bot.command(name='dados_interativo', aliases=['di'])
async def interactive_dice_command(ctx):
    """Comando de texto para abrir interface interativa"""
    view = DiceConfigView()
    embed = view.create_embed()
    await ctx.send(embed=embed, view=view)

@bot.command(name='ajuda_vamp', aliases=['help_vamp', 'vampiro_help'])
async def vampire_help(ctx):
    """Mostra ajuda detalhada sobre o sistema de dados de Vampiro"""
    
    embed = discord.Embed(
        title="🧛 Ajuda - Sistema de Dados Vampiro: A Máscara 5ª Ed",
        description="Como usar o bot de dados para V5",
        color=0x8B0000
    )
    
    embed.add_field(
        name="🎛️ Interface Interativa (NOVO!)",
        value="`/dados` - Abre interface com botões\n`!dados_interativo` ou `!di` - Versão texto",
        inline=False
    )
    
    embed.add_field(
        name="⚡ Comandos Rápidos",
        value="`/vamp <dados> <dificuldade> [fome] [titulo]` - Slash command\n`!vamp <dados> <dificuldade> [fome] [titulo]` - Comando texto\n\nExemplos:\n• `/vamp 5 3 titulo:Teste de Persuasão`\n• `!vamp 6 4 2 Ataque com Garras`",
        inline=False
    )
    
    embed.add_field(
        name="🎯 Como Funciona",
        value="• **Sucessos:** 6-9 = 1 sucesso, 10 = 2 sucessos\n• **Falhas Críticas:** Cada 1 reduz um sucesso da parada\n• **Teste:** Precisa atingir (sucessos totais - falhas críticas) ≥ dificuldade\n• **Fome:** Afeta os primeiros X dados rolados",
        inline=False
    )
    
    embed.add_field(
        name="🩸 Sistema de Fome",
        value="• **Falha Bestial:** 1 nos dados de fome + falha no teste\n• **Sucesso Bestial:** 10 nos dados de fome + falha no teste\n• **Nível:** 0-5 (determina quantos dados são 'de fome')",
        inline=False
    )
    
    embed.add_field(
        name="🎲 Símbolos",
        value="🩸 = Dado de Fome | ✅ = Sucesso (1×) | ❌ = Falha\n💀 = Falha Crítica (reduz sucesso) | ⭐ = Sucesso Crítico (2×)\n🔥 = Potencial Bestial | **Negrito** = Crítico (1 ou 10)",
        inline=False
    )
    
    embed.set_footer(text="💡 Use /dados para a nova interface interativa!")
    
    await ctx.send(embed=embed)

# Tratamento de erros
@roll_vampire.error
async def roll_vampire_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Uso correto: `!vamp <dados> <dificuldade> [fome] [titulo]`\nOu use `/dados` para interface interativa!")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Por favor use números válidos para os parâmetros")

if __name__ == "__main__":
    print("🧛 Iniciando bot de Vampiro: A Máscara...")
    print("💡 Lembre-se de substituir 'SEU_TOKEN_AQUI' pelo token real do seu bot!")
    print("🎛️ Novos recursos: Interface interativa com /dados")
    print("📖 Use !ajuda_vamp para ver todos os comandos")
    
    # IMPORTANTE: Substitua pela sua token real
    bot.run('MTM4MTI5MDk2MjQ2NjExNTY2Ng.GN48rs.7zvRjNpKSxG8u7nIyQ5dMQXi1E_5XocBUVwfyk')