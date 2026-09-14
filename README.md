# AI Security for Developers and Practitioners

## Building safe, trustworthy, and resilient AI systems ##

These instructions will guide you through configuring a GitHub Codespaces environment that you can use to do the labs. 

**1. Change your codespace's default timeout from 30 minutes to longer (60 for half-day sessions, 90 for deep dive sessions).**
To do this, when logged in to GitHub, go to https://github.com/settings/codespaces and scroll down on that page until you see the *Default idle timeout* section. Adjust the value as desired.

![Changing codespace idle timeout value](./images/prompt-accel1.png?raw=true "Changing codespace idle timeout value")

**2. Click on the button below to start a new codespace from this repository.**

Click here ➡️  [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/skillrepos/ai-security?quickstart=1)

**3. Then click on the option to create a new codespace.**

![Creating new codespace from button](./images/prompt-accel2.png?raw=true "Creating new codespace from button")

This will run for a long time while it gets everything ready.

After the initial startup, it will run a script to setup the python environment and install needed python pieces. This will take several more minutes to run. 
The codespace is ready to use when you see a screen like the one shown below in its terminal.

![Ready to use](./images/ai-sec43.png?raw=true "Ready to use")


**4. Open up the *labs.md* file so you can follow along with the labs.**
You can either open it in a separate browser instance or open it in the codespace. 

![Opening labs](./images/ai-security-labs.png?raw=true "Opening labs")

**5. (Optional but recommended) Get a free Groq API key to speed up Lab 2.**

Lab 2 runs a multi-agent system through several reasoning steps. On the local model that takes a few minutes per run; against a hosted model it takes seconds. The lab teaches the same security lessons either way - the controls are the point, not the model - but the faster path is much nicer in a half-day session. The other labs always use the local model and are unaffected.

a. In a browser, go to https://console.groq.com and create an account. (If you get an email with a button to confirm, make sure the link opens in the same browser where you were using Groq. If not, copy the link from the "click here" section and paste it into the right browser.)

b. In the top right of the Groq screen, click on **API Keys**

![API keys](./images/aip55.png?raw=true "API keys")

c. Then click the **Create API Key** button.

![Create API Key](./images/aip56.png?raw=true "Create API Key")

d. Fill in the information, verify you're human if asked, and click **Submit**.

![Create API Key](./images/aip57.png?raw=true "Create API Key")

e. **Copy the key** (you can't view it again later).

![Copy the key](./images/aip58.png?raw=true "Copy the key")

<br><br>

**6. Set your Groq key in the codespace.**

In the codespace **TERMINAL**, run the command below to set your key for all terminals. Paste your key when prompted and then hit *Enter*:

```
source scripts/setup-key.sh
```

Afterwards you should see output confirming that `GROQ_API_KEY` is set.

![Getting API key](./images/aip60.png?raw=true "Getting API key")

If you skip this, everything still works - Lab 2 falls back to the local Ollama model automatically.

<br><br>

**Now, you are ready for the labs!**
