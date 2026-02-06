import os
from openai import OpenAI
import PyPDF2
from datetime import datetime
from dotenv import load_dotenv

# --- RICH UI IMPORTS ---
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import print as rprint

console = Console()
load_dotenv()
client = OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")

def read_pdf(file_path):
    text = ""
    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                content = page.extract_text()
                if content: text += content
        return text
    except Exception as e:
        console.print(f"[bold red]❌ Error reading file:[/bold red] {e}")
        return None

def run_quiz(pdf_context):
    console.print(Panel("[bold yellow]🧠 KNOWLEDGE CHECK[/bold yellow]", subtitle="Multiple Choice Quiz"))
    quiz_prompt = f"Based on these notes: {pdf_context[:4000]}, generate 3 multiple-choice questions. Format: Question, then A), B), C)."
    
    with console.status("[bold cyan]Generating quiz questions...") as status:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": quiz_prompt}]
        )
        quiz_text = response.choices[0].message.content

    console.print(Panel(quiz_text, border_style="yellow"))
    answers = Prompt.ask("[bold cyan]Enter your answers (e.g., ABC)[/bold cyan]")
    
    with console.status("[bold green]Checking answers...") as status:
        check_prompt = f"Quiz:\n{quiz_text}\nStudent Answer: {answers}. Give score/3 and correct answers."
        eval_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": check_prompt}]
        )
        result = eval_response.choices[0].message.content
    
    console.print(Panel(result, title="[bold green]Score Card[/bold green]"))
    return f"\n\nQUIZ RESULTS:\n{result}"

def start_assistant():
    os.system('cls' if os.name == 'nt' else 'clear')
    console.print(Panel.fit("[bold magenta]🎓 PRO AI TUTOR[/bold magenta]\n[italic]Your Intelligent PDF Study Assistant[/italic]", border_style="magenta"))
    
    files = [f for f in os.listdir(".") if f.endswith(".pdf")]
    if not files:
        console.print("[bold red]⚠️ No PDFs found![/bold red] Add a PDF to this folder.")
        return
    
    # Show files in a nice table
    table = Table(title="Available Study Materials", border_style="cyan")
    table.add_column("ID", justify="center")
    table.add_column("File Name", style="green")
    for idx, f in enumerate(files):
        table.add_row(str(idx+1), f)
    console.print(table)

    choice = Prompt.ask("[bold cyan]Type the name of the PDF to study[/bold cyan]")

    if not os.path.exists(choice):
        console.print("[bold red]❌ File not found.[/bold red]")
        return

    pdf_text = read_pdf(choice)
    messages = [{"role": "system", "content": f"You are a helpful tutor. Context: {pdf_text[:8000]}"}]

    console.print(f"[bold green]✅ Loaded {choice}![/bold green] (Type [bold red]'exit'[/bold red] to end)")

    while True:
        user_input = Prompt.ask("\n[bold blue]👤 You[/bold blue]")
        
        if user_input.lower() in ['exit', 'quit', 'done']:
            quiz_report = run_quiz(pdf_text)
            
            # Save logic
            folder = "historic"
            if not os.path.exists(folder): os.makedirs(folder)
            save_path = os.path.join(folder, f"Session_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.txt")
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(f"SESSION: {choice}\n")
                for m in messages[1:]:
                    f.write(f"{m['role'].upper()}: {m['content']}\n\n")
                f.write(quiz_report)
            console.print(f"[bold magenta]📝 Session saved to {folder}. Goodbye![/bold magenta]")
            break

        messages.append({"role": "user", "content": user_input})

        with console.status("[bold blue]Tutor is thinking...") as status:
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages
                )
                answer = response.choices[0].message.content
                console.print(Panel(answer, title="[bold green]🤖 AI Tutor[/bold green]", border_style="green"))
                messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")

if __name__ == "__main__":
    start_assistant()