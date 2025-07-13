#!/usr/bin/env python3
"""
Update Ava's Knowledge Base
Updates the existing OpenAI Assistant with comprehensive Grime Guardians business context
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Load environment variables
load_dotenv()

async def update_ava_knowledge():
    """Update Ava's OpenAI Assistant with complete business knowledge."""
    
    print("🧠 Updating Ava's Knowledge Base with Grime Guardians Context")
    print("=" * 65)
    
    try:
        from src.agents.ava_assistant import ava_assistant
        
        print("✅ Ava Assistant imported successfully")
        
        # Initialize to get the assistant ID
        await ava_assistant._initialize_assistant()
        
        if not ava_assistant.assistant_id:
            print("❌ No assistant found to update")
            return
            
        print(f"🔍 Found Assistant ID: {ava_assistant.assistant_id}")
        
        # Get the new comprehensive instructions
        new_instructions = ava_assistant._get_system_instructions()
        new_tools = ava_assistant._get_function_tools()
        
        print("📝 Updating assistant with comprehensive Grime Guardians knowledge...")
        
        # Update the assistant
        updated_assistant = await ava_assistant.client.beta.assistants.update(
            assistant_id=ava_assistant.assistant_id,
            instructions=new_instructions,
            tools=new_tools
        )
        
        print("✅ Assistant updated successfully!")
        print(f"📊 Instructions length: {len(new_instructions)} characters")
        print(f"🔧 Function tools: {len(new_tools)} tools available")
        
        print("\n🎯 New Knowledge Includes:")
        print("   • Complete Grime Guardians business context")
        print("   • Actual SOP for photo submissions and checklists")
        print("   • Team structure and compensation details")
        print("   • Pricing structure and policies")
        print("   • 3-strike enforcement system")
        print("   • Quality standards and requirements")
        print("   • Geographic preferences for cleaners")
        print("   • Sales and marketing protocols")
        
        # Test the updated knowledge
        print("\n🧪 Testing Updated Knowledge...")
        
        # Create a test thread
        thread = await ava_assistant.client.beta.threads.create()
        
        # Test question about SOP
        test_question = "What's our SOP for photo submissions and checklists?"
        
        await ava_assistant.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=test_question
        )
        
        # Run the assistant
        run = await ava_assistant.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ava_assistant.assistant_id
        )
        
        # Wait for completion
        while run.status in ["queued", "in_progress"]:
            await asyncio.sleep(1)
            run = await ava_assistant.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
        
        if run.status == "completed":
            # Get the response
            messages = await ava_assistant.client.beta.threads.messages.list(
                thread_id=thread.id,
                order="desc",
                limit=1
            )
            
            if messages.data:
                response = messages.data[0].content[0].text.value
                print(f"\n📋 Test Response Preview:")
                print(f"   Question: {test_question}")
                print(f"   Response: {response[:200]}...")
                
                # Check if it includes Grime Guardians specific info
                grime_specific = any(term in response.lower() for term in [
                    "grime guardians", "🚗 arrived", "🏁 finished", "3-strike", 
                    "$10 deduction", "kitchen, bathrooms, entry area"
                ])
                
                if grime_specific:
                    print("   ✅ Response includes Grime Guardians-specific information!")
                else:
                    print("   ⚠️ Response may still be generic")
        
        print(f"\n✅ Ava's knowledge base successfully updated!")
        print("💡 She now has complete context about Grime Guardians operations")
        
    except Exception as e:
        print(f"❌ Update failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(update_ava_knowledge())