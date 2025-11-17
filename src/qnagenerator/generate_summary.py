import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from datetime import datetime

st.set_page_config(page_title="Transcript Summary Generator", page_icon="📝", layout="centered")

st.title("📝 Transcript Summary Generator")
st.write("Upload a transcript and generate a detailed summary with key points")

# Load prompts
@st.cache_resource
def load_prompt():
    try:
        with open("prompt.md", "r") as f:
            return f.read()
    except FileNotFoundError:
        st.error("❌ prompt.md file not found!")
        return None

prompt_content = load_prompt()

# Model selection (Zephyr-7B is best for summarization)
MODEL_NAME = "HuggingFaceH4/zephyr-7b-beta"

# File upload
uploaded_file = st.file_uploader("Upload transcript (.txt file)", type=["txt"])

if uploaded_file:
    transcript_text = uploaded_file.read().decode("utf-8")
    st.success(f"✅ File uploaded: {uploaded_file.name}")
    st.info(f"📄 Transcript length: {len(transcript_text)} characters")

if st.button("🔄 Generate Summary", type="primary", use_container_width=True):
    if not prompt_content:
        st.error("❌ Could not load prompt file")
    elif not uploaded_file:
        st.error("❌ Please upload a transcript file first")
    else:
        with st.spinner("⏳ Generating summary... (This may take 2-3 minutes)"):
            try:
                # Parse prompt - only System Prompt now
                system_prompt = prompt_content.strip()
                
                # Create user message with transcript
                user_message = f"Summarize this transcript:\n\n{transcript_text[:4000]}"
                
                # Load model with memory optimization
                st.info("📥 Loading Zephyr-7B model...")
                tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
                
                device = "cuda" if torch.cuda.is_available() else "cpu"
                model = AutoModelForCausalLM.from_pretrained(
                    MODEL_NAME,
                    dtype=torch.float16
                ).to(device)
                
                st.info(f"⚙️ Generating summary on {device.upper()}...")
                
                # Prepare messages with system prompt
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
                inputs = tokenizer.apply_chat_template(
                    messages,
                    add_generation_prompt=True,
                    tokenize=True,
                    return_dict=True,
                    return_tensors="pt",
                ).to(device)
                
                # Generate with optimized settings
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=1000,  # Reduced from 1500
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
                
                # Clear cache
                torch.cuda.empty_cache()
                
                # Decode
                summary = tokenizer.decode(
                    outputs[0][inputs["input_ids"].shape[-1]:],
                    skip_special_tokens=True
                )
                
                # Display summary
                st.success("✅ Summary Generated!")
                st.divider()
                st.markdown(summary)
                st.divider()
                
                # Download button
                st.download_button(
                    label="📥 Download Summary",
                    data=summary,
                    file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("💡 Tips: Use GPU for faster processing. CPU will be slow.")
