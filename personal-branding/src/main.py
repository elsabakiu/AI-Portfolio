import os
from dotenv import load_dotenv
from document_processor import DocumentProcessor
from llm_integration import LLMIntegration
from prompt_templates import PromptTemplates
from human_voice_engine import HumanVoiceEngine

# Load environment variables
load_dotenv()

class PersonalBrandContentCreator:
    def __init__(self):
        print("🚀 Initializing Personal Brand Content Creator...")
        
        # Initialize components
        self.doc_processor = DocumentProcessor()
        self.llm = LLMIntegration(api_key=os.getenv("OPENAI_API_KEY"))
        self.templates = PromptTemplates()
        self.human_voice = HumanVoiceEngine()
        
        # Load knowledge bases
        self.load_knowledge_bases()
    
    def load_knowledge_bases(self):
        """Load your personal brand documents"""
        print("\n📚 Loading your personal brand knowledge...")
        self.doc_processor.load_all()
        print("✅ Ready to create content!\n")
    
    def create_with_human_voice(self, template_type: str, topic: str):
        """Generate content using the human voice engine"""
        print(f"🔍 Finding relevant context for: '{topic}'")
        context = self.doc_processor.search(topic)
        
        # Add human voice system prompt
        system_prompt = self.human_voice.get_system_prompt()
        
        # Select the right template
        if template_type == "observation":
            template = self.human_voice.get_observation_post_template()
        elif template_type == "pattern":
            template = self.human_voice.get_pattern_recognition_template()
        elif template_type == "contrast":
            template = self.human_voice.get_market_contrast_template()
        else:
            template = self.human_voice.get_observation_post_template()
        
        # Combine system prompt with template
        full_prompt = f"{system_prompt}\n\n{template.format(context=context, topic=topic)}"
        
        print("✍️ Writing with human consulting voice...")
        return self.llm.generate(full_prompt, temperature=0.8)
    
    def check_authenticity(self, content: str):
        """Check if content passes the anti-GPT test"""
        check_prompt = self.human_voice.get_authenticity_check().format(content=content)
        return self.llm.generate(check_prompt)
    
    def rewrite_content(self, content: str):
        """Rewrite generic content with human voice"""
        rewrite_prompt = self.human_voice.rewrite_with_human_voice().format(content=content)
        return self.llm.generate(rewrite_prompt)

def main():
    # Create the content creator
    creator = PersonalBrandContentCreator()
    
    # Interactive menu
    while True:
        print("\n" + "="*50)
        print("PERSONAL BRAND LINKEDIN CONTENT CREATOR")
        print("="*50)
        print("HUMAN CONSULTING VOICE - ANTI-GPT ENGINE")
        print("-"*50)
        print("1. Observation Post (Real observation → Unexpected angle → Example → Open implication)")
        print("2. Pattern Recognition Post (Pattern → Assumption → Reality → Why it matters)")
        print("3. Market Contrast Post (Two environments → Behavioral difference → Outcome)")
        print("4. Check content authenticity (Anti-GPT test)")
        print("5. Rewrite generic content with human voice")
        print("6. Exit")
        
        choice = input("\nChoose an option (1-6): ")
        
        if choice == "6":
            print("👋 Good luck with your personal brand!")
            break
        
        if choice == "4":
            content = input("Paste your content to check: ")
            result = creator.check_authenticity(content)
            print("\n" + "="*50)
            print("AUTHENTICITY CHECK:")
            print("="*50)
            print(result)
            
        elif choice == "5":
            content = input("Paste generic content to rewrite: ")
            result = creator.rewrite_content(content)
            print("\n" + "="*50)
            print("REWRITTEN WITH HUMAN VOICE:")
            print("="*50)
            print(result)
            
        else:
            topic = input("What topic do you want to post about? ")
            
            if choice == "1":
                content = creator.create_with_human_voice("observation", topic)
                print("\n" + "="*50)
                print("YOUR OBSERVATION POST:")
                print("="*50)
            elif choice == "2":
                content = creator.create_with_human_voice("pattern", topic)
                print("\n" + "="*50)
                print("YOUR PATTERN RECOGNITION POST:")
                print("="*50)
            elif choice == "3":
                content = creator.create_with_human_voice("contrast", topic)
                print("\n" + "="*50)
                print("YOUR MARKET CONTRAST POST:")
                print("="*50)
            
            print(content)
            
            # Optional authenticity check
            check = input("\nRun authenticity check? (y/n): ")
            if check.lower() == 'y':
                result = creator.check_authenticity(content)
                print("\n" + "-"*30)
                print(result)
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()