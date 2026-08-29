#!/usr/bin/env python3
"""
Hyprland Fast Emoji Picker
Searches and copies Unicode emojis to clipboard and simulates typing via wtype if available.
"""

import sys
import shutil
import subprocess

EMOJIS = [
    # Smileys & Emotion
    ("😀", "Grinning Face", "smile happy grin"),
    ("😃", "Grinning Face With Big Eyes", "smile happy joy"),
    ("😄", "Grinning Face With Smiling Eyes", "smile happy joy laugh"),
    ("😁", "Beaming Face With Smiling Eyes", "grin happy smile"),
    ("😆", "Grinning Squinting Face", "laugh haha lol"),
    ("😅", "Grinning Face With Sweat", "hot nervous phew"),
    ("🤣", "Rolling on the Floor Laughing", "rofl lol haha lmao"),
    ("😂", "Face With Tears of Joy", "laugh haha lol cry joy"),
    ("🙂", "Slightly Smiling Face", "smile ok fine"),
    ("🙃", "Upside-Down Face", "sarcasm ironical silly"),
    ("😉", "Winking Face", "wink flirt joke"),
    ("😊", "Smiling Face With Smiling Eyes", "blush happy warm"),
    ("😇", "Smiling Face With Halo", "angel innocent pure"),
    ("🥰", "Smiling Face With Hearts", "love affection adore"),
    ("😍", "Smiling Face With Heart-Eyes", "love romance crush"),
    ("🤩", "Star-Struck", "excited wow amazing"),
    ("😘", "Face Blowing a Kiss", "kiss love romance"),
    ("😋", "Face Savoring Food", "delicious yummy taste nom"),
    ("😛", "Face With Tongue", "tongue silly playful"),
    ("😜", "Winking Face With Tongue", "playful silly crazy"),
    ("🤪", "Zany Face", "wild party crazy goofy"),
    ("😝", "Squinting Face With Tongue", "playful pranking"),
    ("🤑", "Money-Mouth Face", "rich cash dollar profit"),
    ("🤗", "Smiling Face With Open Hands", "hug affection embrace"),
    ("🤭", "Face With Hand Over Mouth", "oops quiet giggle"),
    ("🤫", "Shushing Face", "quiet secret hush shh"),
    ("🤔", "Thinking Face", "hmm think wonder ponder"),
    ("🤐", "Zipper-Mouth Face", "silent secret quiet"),
    ("🤨", "Face With Raised Eyebrow", "suspicious doubt skeptical"),
    ("😐", "Neutral Face", "meh pokerface straight"),
    ("😑", "Expressionless Face", "deadpan blank annoyed"),
    ("😶", "Face Without Mouth", "speechless silence blank"),
    ("😏", "Smirking Face", "smirk playful confident flirt"),
    ("😒", "Unamused Face", "annoyed dissatisfied unimpressed"),
    ("🙄", "Face With Rolling Eyes", "eyeroll whatever bored"),
    ("😬", "Grimacing Face", "awkward nervous cringe"),
    ("🤥", "Lying Face", "pinocchio lie dishonest"),
    ("😌", "Relieved Face", "peace calm chill relaxed"),
    ("😔", "Pensive Face", "sad reflective down"),
    ("😪", "Sleepy Face", "tired sleep yawn"),
    ("🤤", "Drooling Face", "drool crave hungry"),
    ("😴", "Sleeping Face", "zzz sleep tired goodnight"),
    ("😷", "Face With Medical Mask", "sick illness flu mask"),
    ("🤒", "Face With Thermometer", "sick fever ill temperature"),
    ("🤕", "Face With Head-Bandage", "hurt injured wound head"),
    ("🤢", "Nauseated Face", "gross sick vomit green"),
    ("🤮", "Face Vomiting", "puke sick gross barf"),
    ("🤧", "Sneezing Face", "sneeze cold allergy"),
    ("🥵", "Hot Face", "heat fever sunburn warm"),
    ("🥶", "Cold Face", "freeze ice cold winter"),
    ("🥴", "Woozy Face", "drunk dizzy tipsy confused"),
    ("😵", "Face With Crossed-Out Eyes", "dead dizzy knocked out"),
    ("🤯", "Exploding Head", "mind blown shock unbelievable"),
    ("🥳", "Partying Face", "celebration party birthday yay"),
    ("😎", "Smiling Face With Sunglasses", "cool swag awesome chill"),
    ("🤓", "Nerd Face", "geek smart glasses study"),
    ("🧐", "Face With Monocle", "curious investigate classy"),
    ("😕", "Confused Face", "unsure puzzled what"),
    ("😟", "Worried Face", "anxious nervous concerned"),
    ("🙁", "Slightly Frowning Face", "sad unhappy disappointed"),
    ("😮", "Face With Open Mouth", "surprised wow gasp"),
    ("😯", "Hushed Face", "shocked quiet astonished"),
    ("😲", "Astonished Face", "shocked amazed gasped"),
    ("😳", "Flushed Face", "embarrassed blush stunned"),
    ("🥺", "Pleading Face", "puppy eyes please begging cute"),
    ("😦", "Frowning Face With Open Mouth", "aw dismayed distressed"),
    ("😧", "Anguished Face", "shock horror painful"),
    ("😨", "Fearful Face", "scared afraid panic terror"),
    ("😰", "Anxious Face With Sweat", "nervous blue scared sweat"),
    ("😥", "Sad But Relieved Face", "phew stress close call"),
    ("😢", "Crying Face", "tear sad sorrow weep"),
    ("😭", "Loudly Crying Face", "sob weeping tears scream"),
    ("😱", "Face Screaming in Fear", "horror scream terror munch"),
    ("😖", "Confounded Face", "frustrated struggling upset"),
    ("😣", "Persevering Face", "endure struggle pain"),
    ("😞", "Disappointed Face", "sad let down regret"),
    ("😓", "Downcast Face With Sweat", "stressed work overwhelmed"),
    ("😩", "Weary Face", "tired exhausted groan"),
    ("😫", "Tired Face", "exhausted stressed fed up"),
    ("🥱", "Yawning Face", "sleepy tired bored"),
    ("😤", "Face With Steam From Nose", "huff angry triumph determined"),
    ("😡", "Enraged Face", "angry mad fury red"),
    ("😠", "Angry Face", "mad annoyed irritated"),
    ("🤬", "Face With Symbols on Mouth", "swear curse angry swearwords"),
    ("😈", "Smiling Face With Horns", "devil mischievous evil prank"),
    ("👿", "Angry Face With Horns", "devil demon furious"),
    ("💀", "Skull", "dead skeleton danger rip lol"),
    ("☠️", "Skull and Crossbones", "danger poison pirate death"),
    ("💩", "Pile of Poo", "poop turd crap joke"),
    ("🤡", "Clown Face", "clown fool circus funny"),
    ("👻", "Ghost", "spooky phantom boo halloween"),
    ("👽", "Alien", "ufo extraterrestrial sci-fi"),
    ("👾", "Alien Monster", "arcade retro 8bit pixel gaming"),
    ("🤖", "Robot", "bot artificial intelligence ai tech"),

    # Hand Gestures & People
    ("👋", "Waving Hand", "hello bye hi wave cya"),
    ("🤚", "Raised Back of Hand", "stop hand high five"),
    ("🖐️", "Hand With Fingers Splayed", "five hand open"),
    ("✋", "Raised Hand", "stop high five halt pause"),
    ("🖖", "Vulcan Salute", "spock star trek live long prosper"),
    ("👌", "OK Hand", "perfect alright agreed good"),
    ("🤌", "Pinched Fingers", "italian gesture what you want"),
    ("🤏", "Pinching Hand", "little small tiny bit"),
    ("✌️", "Victory Hand", "peace two victory v"),
    ("🤞", "Crossed Fingers", "luck hope wish fingers crossed"),
    ("🤟", "Love-You Gesture", "ily love rock hand"),
    ("🤘", "Sign of the Horns", "rock metal concert cool"),
    ("🤙", "Call Me Hand", "shaka phone hang loose"),
    ("👈", "Backhand Index Pointing Left", "left point direction"),
    ("👉", "Backhand Index Pointing Right", "right point direction"),
    ("👆", "Backhand Index Pointing Up", "up point direction north"),
    ("🖕", "Middle Finger", "fu offensive flip off"),
    ("👇", "Backhand Index Pointing Down", "down point south"),
    ("☝️", "Index Pointing Up", "one attention listen point"),
    ("👍", "Thumbs Up", "like approve good yes agree +1"),
    ("👎", "Thumbs Down", "dislike disapprove bad no -1"),
    ("✊", "Raised Fist", "power solidarity strength punch"),
    ("👊", "Oncoming Fist", "fist bump punch bro hit"),
    ("🤛", "Left-Facing Fist", "fist bump left"),
    ("🤜", "Right-Facing Fist", "fist bump right"),
    ("👏", "Clapping Hands", "applause bravo cheer clap"),
    ("🙌", "Raising Hands", "celebrate praise hooray yay"),
    ("👐", "Open Hands", "open jazz hands welcome"),
    ("🤲", "Palms Up Together", "pray offering hope"),
    ("🤝", "Handshake", "deal agreement partner meet"),
    ("🙏", "Folded Hands", "please pray thank you thanks namaste"),
    ("✍️", "Writing Hand", "write author pen note document"),
    ("💅", "Nail Polish", "care beauty glam slay sassy"),
    ("🤳", "Selfie", "phone camera photo selfie"),
    ("💪", "Flexed Biceps", "muscle strong fitness gym power"),

    # Hearts & Symbols
    ("❤️", "Red Heart", "love passion romance like"),
    ("🧡", "Orange Heart", "warmth friendship care"),
    ("💛", "Yellow Heart", "joy sunshine pure friendship"),
    ("💚", "Green Heart", "nature envy health organic"),
    ("💙", "Blue Heart", "trust calm loyalty peace"),
    ("💜", "Purple Heart", "royalty luxury style charm"),
    ("🖤", "Black Heart", "dark goth emo sorrow"),
    ("🤍", "White Heart", "pure clean peace innocent"),
    ("🤎", "Brown Heart", "earth cozy warm"),
    ("💔", "Broken Heart", "sad break heartbreak sorrow"),
    ("❣️", "Heart Exclamation", "emphasis love punctuation"),
    ("💕", "Two Hearts", "love affection floating hearts"),
    ("💞", "Revolving Hearts", "love romance moving"),
    ("💓", "Beating Heart", "pulse alive heartbeat"),
    ("💗", "Growing Heart", "expanding love affection"),
    ("💖", "Sparkling Heart", "sparkle magic shiny love"),
    ("💘", "Heart With Arrow", "cupid romance fall in love"),
    ("💝", "Heart With Ribbon", "gift present love special"),
    ("🔥", "Fire", "lit hot flame burn awesome cool"),
    ("💥", "Collision", "boom explode crash blast"),
    ("✨", "Sparkles", "magic clean shiny special star"),
    ("⭐", "Star", "favorite rate gold stellar rating"),
    ("🌟", "Glowing Star", "sparkle shine bright outstanding"),
    ("💫", "Dizzy Symbol", "star motion dizzy sparkle"),
    ("⚡", "High Voltage", "lightning power electric fast energy"),
    ("🎉", "Party Popper", "celebration congrats birthday victory"),
    ("🎊", "Confetti Ball", "festive party celebration yay"),
    ("🎯", "Bullseye", "target goal direct hit accurate"),
    ("🚀", "Rocket", "launch fast growth space ship moon"),
    ("💡", "Light Bulb", "idea smart invention inspiration"),
    ("📌", "Pushpin", "pin notice memo mark save"),
    ("📍", "Round Pushpin", "location map spot here place"),
    ("📎", "Paperclip", "attachment document file clip"),
    ("🔍", "Magnifying Glass Tilted Left", "search find inspect lookup"),
    ("🔒", "Locked", "security private safe closed encrypt"),
    ("🔓", "Unlocked", "open access security free"),
    ("🔑", "Key", "password token access unlock secret"),
    ("🛡️", "Shield", "security protect defense guard"),
    ("⚙️", "Gear", "settings config preferences tool options"),
    ("🛠️", "Hammer and Wrench", "build fix tools developer maintenance"),
    ("💻", "Laptop Computer", "coding pc tech programming macbook"),
    ("🖥️", "Desktop Computer", "screen monitor pc setup workstation"),
    ("📱", "Mobile Phone", "cell smartphone iphone android"),
    ("🔋", "Battery", "power charge energy electrical"),
    ("🌐", "Globe With Meridians", "internet world web website online"),
    ("📦", "Package", "box shipment parcel deliver git"),
    ("☕", "Hot Beverage", "coffee tea morning caffeine espresso"),
    ("🍺", "Beer Mug", "drink cheers pub alcohol party"),
    ("🍕", "Pizza", "food slice cheese dinner lunch"),
    ("🍔", "Hamburger", "burger fast food snack food"),
    ("🍿", "Popcorn", "movie theater snack cinema drama"),

    # Flags & Badges
    ("✅", "Check Mark Button", "done complete correct success pass ok"),
    ("❌", "Cross Mark", "fail error wrong cancel decline no"),
    ("⚠️", "Warning", "alert caution danger attention notice"),
    ("⛔", "No Entry", "forbidden stop blocked denied"),
    ("🚫", "Prohibited", "no banned restricted disallowed"),
    ("💯", "Hundred Points", "score perfect 100 excellent full"),
    ("🏆", "Trophy", "champion winner first prize award gold"),
    ("🥇", "1st Place Medal", "gold winner first place victory"),
    ("🥈", "2nd Place Medal", "silver second runner up"),
    ("🥉", "3rd Place Medal", "bronze third third place"),
    ("🚩", "Triangular Flag", "red flag danger mark milestone goal"),
    ("🏁", "Chequered Flag", "finish line race complete ready start")
]

def main():
    lines = [f"{emoji}  {name}  ({tags})" for emoji, name, tags in EMOJIS]
    input_text = "\n".join(lines)

    # Launch Fuzzel or Wofi
    if shutil.which("fuzzel"):
        cmd = ["fuzzel", "--dmenu", "--prompt", "Emoji: ", "--width", "42", "--lines", "12"]
    elif shutil.which("wofi"):
        cmd = ["wofi", "--dmenu", "--prompt", "Search Emoji...", "--width", "480", "--height", "380", "--insensitive"]
    else:
        sys.exit(1)

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    selected, _ = proc.communicate(input=input_text)
    selected = selected.strip()

    if not selected:
        return

    # Extract emoji character (first element before double spaces)
    emoji_char = selected.split(" ")[0].strip()
    if not emoji_char:
        return

    # Copy to clipboard
    if shutil.which("wl-copy"):
        p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE, text=True)
        p.communicate(input=emoji_char)

    # Optionally auto-type using wtype or ydotool if running
    if shutil.which("wtype"):
        subprocess.run(["wtype", emoji_char])
    elif shutil.which("notify-send"):
        subprocess.Popen([
            "notify-send",
            "-a", "Emoji Picker",
            "-i", "accessories-character-map",
            "-t", "2000",
            f"Copied {emoji_char}",
            "Emoji copied to clipboard."
        ])

if __name__ == "__main__":
    main()
