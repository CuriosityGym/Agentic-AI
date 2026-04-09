"""
chat_handler.py — Core logic that connects user messages to the AI agent.

What this file does:
    1. Detects whether a user message contains a YouTube URL
    2. Fetches the transcript if a new video URL is found
    3. Sends the message + transcript to the Langflow agent
    4. Returns the updated conversation history and state

Students: The stretch feature in app.py calls send_to_agent() from this file.
          Understanding send_to_agent() is the key to building your own
          stretch features — any button that needs to talk to the AI should
          call this function.
"""

# Use this only to debug the UI without making real API calls. It contains a snippet of a real
sample_transcript = """
hello this video will guide you on how to build your student portfolio on mysphere a portfolio is a collection of projects it is a digital showcase of your best work and skills exercised while working on different projects if you have created projects in school college or in a course you can make them a part of your portfolio a portfolio is a part of your student profile and is also included in your dynamic cv now let's see how you can add projects to build your portfolio sign in to your my sphere account click on the portfolio option from your profile drop-down menu on your portfolio dashboard some sample projects are added for your reference to add a new project click on the create project block let's start creating a new project now adding the name of the project is a must next you can upload a suitable cover photo that depicts what the project is about from the top right hand corner you can do the settings for this project whether to keep it private or make it public in the creator field your profile name would be shown automatically next you can add the date when the project was done and the subject for example engineering electronics or science and write the name of your project guide or mentor in the guidance by field add names of your project team members and enlist the tools used for that project for example a milling machine welding machine and a few others have been listed here you can also add relevant keywords or key terms in a project tags field coming to the objective field now write about the key goals that were planned for the project now let's move to the description field to write the project outline and steps followed the conclusion and anything you would like to describe can be written here gather your learnings and note them in the key learnings field it could be new methods or techniques your reflection on what worked well and what didn't and how you led the project you can add multiple types of attachments to your projects based on how it helps explain your project in the best possible way you can add text big images images with a corresponding text a carousel and video assets all these make the project visually appealing and help viewers better understand your project one thing to remember while adding attachments whether images videos or text appear in the order they have been uploaded let's have a look at each type of project attachment if you select the text option you get a text field above the attachment options you can add more information about the project expand on project objectives or your learnings in this space you can also add a big image depicting the outcome of your project there is also an option image and text wherein you can add an image with a summary or short description next to it adding video to your project makes it easier to understand how the project was done you can upload a video that shows either the project presentation or steps shown in a time-lapse manner or a quick walkthrough of the project timeline or try other ideas you have for making a project video next comes an interesting feature called a carousel or image slider you can add a maximum of 10 images you can use it to explain steps followed in the project or sequential progress note that the images will be shown in the order you have uploaded them so make sure to decide the order in which you want them to appear before you start uploading images in the carousel format once you have added all the project details along with multimedia you can click on the preview button and check all the details you have added perhaps proofread and then hit the save button there you go you have your project ready to showcase in your portfolio likewise you can add multiple projects and have your impressive student portfolio ready
"""

import uuid

from transcript import extract_youtube_url, extract_video_id, fetch_transcript
from langflow_client import call_langflow


# ════════════════════════════════════════════════════════════════════════════
# CORE: send_to_agent
# Send any pre-built message to the AI and get back the updated chat history.
# ─────────────────────────────────────────────────────────────────────────────
# All stretch features call this instead of calling call_langflow() directly.
# This keeps each stretch feature short and focused on its own logic.
# ════════════════════════════════════════════════════════════════════════════

def send_to_agent(
    user_message: str,
    history: list,
    transcript_state: str,
    session_id: str,
) -> tuple:
    """
    Send a message to the Langflow agent and return the updated chat history.

    Unlike respond(), this function skips YouTube URL detection. Use it when
    you already have a fully formed message ready to send — for example from
    a stretch feature like the prerequisites prompt.

    Returns:
        (updated_history, transcript_state, session_id, status_text)
    """
    try:
        ai_reply = call_langflow(user_message, session_id)
    except Exception as exc:
        history = history + [
            {"role": "user",      "content": user_message},
            {"role": "assistant", "content": f"**AI error:** {exc}"},
        ]
        return history, transcript_state, session_id, f"Error: {exc}"

    history = history + [
        {"role": "user",      "content": user_message},
        {"role": "assistant", "content": ai_reply},
    ]
    return history, transcript_state, session_id, "Ready"


# ════════════════════════════════════════════════════════════════════════════
# CORE: respond
# Main chat handler — called every time the user clicks Send or presses Enter.
# ════════════════════════════════════════════════════════════════════════════

def respond(
    user_message: str,
    history: list,
    transcript_state: str,
    session_id: str,
) -> tuple:
    """
    Main handler wired to the Send button and the Enter key in the UI.

    Flow:
      - Message contains a YouTube URL → fetch transcript → summarise
      - No URL, transcript already loaded → follow-up question
      - No URL, no transcript → ask the user to share a link first

    Returns:
        (updated_history, transcript_state, session_id, status_text)
    """
    if not user_message.strip():
        return history, transcript_state, session_id, "Ready"

    youtube_url = extract_youtube_url(user_message)

    # ── New video URL detected ────────────────────────────────────────────
    if youtube_url:
        video_id = extract_video_id(youtube_url)
        if not video_id:
            history = history + [
                {"role": "user", "content": user_message},
                {
                    "role": "assistant",
                    "content": (
                        "I couldn't recognise a valid YouTube video ID in that link. "
                        "Try `https://youtu.be/VIDEO_ID` or "
                        "`https://www.youtube.com/watch?v=VIDEO_ID`."
                    ),
                },
            ]
            return history, transcript_state, session_id, "Invalid URL"

        # New video → fresh session ID so Langflow memory doesn't carry over
        new_session_id = str(uuid.uuid4())

        try:
            transcript = fetch_transcript(youtube_url)
            # transcript = sample_transcript # Use this line instead of the above to avoid real API calls while testing or debugging the UI
        except Exception as exc:
            history = history + [
                {"role": "user",      "content": user_message},
                {"role": "assistant", "content": f"**Transcript error:** {exc}"},
            ]
            return history, transcript_state, session_id, f"Error: {exc}"

        try:
            ai_reply = call_langflow(user_message, new_session_id, transcript)
        except Exception as exc:
            history = history + [
                {"role": "user",      "content": user_message},
                {"role": "assistant", "content": f"**AI error:** {exc}"},
            ]
            return history, transcript, new_session_id, f"Error: {exc}"

        history = history + [
            {"role": "user",      "content": user_message},
            {"role": "assistant", "content": ai_reply},
        ]
        word_count = len(transcript.split())
        return history, transcript, new_session_id, f"Ready — transcript: {word_count:,} words"

    # ── No URL: treat as a follow-up question ─────────────────────────────
    if not transcript_state:
        history = history + [
            {"role": "user", "content": user_message},
            {
                "role": "assistant",
                "content": (
                    "Please start by sharing a YouTube link so I can fetch the transcript. "
                    "Example: *Here is https://youtu.be/xyz — can you summarise it?*"
                ),
            },
        ]
        return history, transcript_state, session_id, "Waiting for video link"

    return send_to_agent(user_message, history, transcript_state, session_id)


# ════════════════════════════════════════════════════════════════════════════
# CORE: clear_chat
# Reset everything so the user can start a fresh conversation.
# ════════════════════════════════════════════════════════════════════════════

def clear_chat(transcript_state, session_id):
    """
    Clear the chat and generate a new session ID.
    A new session ID ensures Langflow memory starts completely fresh.
    """
    return [], "", str(uuid.uuid4()), "Cleared — ready for a new video"