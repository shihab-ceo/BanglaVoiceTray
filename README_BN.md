# Bangla Voice Tray (Windows 11) · v1.1.0

একটি ছোট system-tray অ্যাপের প্রাথমিক সোর্স প্রজেক্ট। ডিফল্ট শর্টকাট `Ctrl+Shift+B` দিয়ে বাংলা ডিকটেশন চালু/বন্ধ করা যায়। লেখা clipboard/paste দিয়ে বর্তমান কার্সর অবস্থানে পাঠানোর চেষ্টা করে।

## প্রয়োজনীয়তা
- Windows 11, Python 3.11 বা 3.12 (64-bit) সুপারিশ করা হয়
- ইন্টারনেট
- মাইক্রোফোন
- Windows-এ microphone privacy permission চালু

## চালানোর পদ্ধতি
1. Python ইনস্টল করার সময় **Add Python to PATH** নির্বাচন করুন।
2. ZIP extract করুন।
3. `run_from_source.bat` চালান। প্রথমবার Python packages ইনস্টল হবে।
4. সিস্টেম ট্রে-তে মাইক্রোফোন আইকন দেখুন। আইকনে left-click করলে শোনা চালু/বন্ধ হবে; চালু হলে আইকন লাল, বন্ধ হলে নীল দেখাবে।
5. Notepad খুলে কার্সর রাখুন, তারপর ডিফল্ট `Ctrl+Shift+B` চাপুন। বন্ধ করতে একই shortcut আবার চাপুন।
6. Tray icon-এ right-click করে **অবস্থা ও শর্টকাট দেখুন** অথবা **সেটিংস** খুলুন। Microphone, shortcut, ভাষা, input device, paste delay, Windows startup ও window transparency একই control window-তে পাবেন।
7. Shortcut বদলাতে edit বোতাম চাপুন, নতুন key combination দিন, তারপর সংরক্ষণ করুন। Transparency slider সরালে window-র opacity সঙ্গে সঙ্গে বদলায়। Permission না থাকলে **মাইক্রোফোন permission খুলুন** চাপুন।

## EXE তৈরি
`build_exe.bat` চালান। সফল হলে `dist\BanglaVoiceTray.exe` তৈরি হবে।

## গুরুত্বপূর্ণ সীমাবদ্ধতা
- অনলাইন Google Speech Recognition ব্যবহার করে; অডিও ইন্টারনেটের মাধ্যমে তৃতীয়-পক্ষের সেবায় প্রক্রিয়াকৃত হয়। গোপন/সংবেদনশীল কথা ডিকটেট করবেন না।
- ফ্রি API ব্যবহারে সেবা/নেটওয়ার্কের সীমাবদ্ধতা হতে পারে; এটি কোনো গ্যারান্টিযুক্ত SLA নয়।
- Windows-এর `Ctrl+Shift+Esc` হলো Task Manager খোলার সিস্টেম শর্টকাট। এই অ্যাপ সেটি দেখায়; Task Manager-এর নিজস্ব UI-তে অ্যাপের শর্টকাট দেখাতে পারে না।
- Global hotkey library `keyboard` কিছু সিস্টেমে সীমাবদ্ধ হতে পারে। সমস্যা হলে `app.log` দেখুন।
- clipboard/paste সব elevated/admin অ্যাপ বা সুরক্ষিত টেক্সট বক্সে কাজ নাও করতে পারে।
- Settings-এর **মাইক্রোফোন permission খুলুন** বোতাম Windows-এর Microphone privacy পৃষ্ঠা খুলবে। Windows-এ একাধিক mic থাকলে Settings-এর dropdown থেকে এই অ্যাপের জন্য একটি input device বাছুন; একসঙ্গে একটিই mic ব্যবহার হয়।
- `Ctrl+Shift+B` অন্য অ্যাপেও ব্যবহৃত হলে Settings-এ অন্য শর্টকাট বেছে নিন।
- এটি একটি starter project; ব্যবহার করার আগে নিজের কম্পিউটারে পরীক্ষা করুন।

## ফাইল
- `main.py`: tray, recognition ও application lifecycle
- `modern_ui.py`: Qt control window এবং এক-জানালার UI
- `requirements.txt`: Python dependencies
- `run_from_source.bat`: সোর্স থেকে চালানো
- `build_exe.bat`: Windows EXE তৈরি
- সেটিংস/লগ: `%APPDATA%\BanglaVoiceTray\`

## নিরাপত্তা
সোর্স কোড দেখে নিন। প্রথমবার চালানোর সময় Windows Defender/SmartScreen সতর্কতা দেখালে যাচাই না করে bypass করবেন না।



## v1.1.0 UI আপডেট

- পুরোনো আলাদা dashboard/settings window-এর বদলে এক compact control window।
- Rounded cyan/blue glow cards, shadow, aligned controls ও বড় shortcut text।
- Live window transparency slider; মানটি config-এ সংরক্ষিত হয়।
- Microphone, shortcut, language, input, paste delay, startup ও permission controls একই window-তে।

Qt Widgets-এর জন্য `PySide6-Essentials` dependency যোগ হয়েছে। Audio, tray icon, global shortcut ও paste workflow আগের মতোই রাখা হয়েছে।
