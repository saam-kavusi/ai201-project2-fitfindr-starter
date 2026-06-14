# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
`search_listings` searches the mock secondhand listings dataset for items that match the user's requested description, optional size, and optional max price. It returns matching listings for the agent to choose from, or an empty list if nothing matches.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): The user's natural language search phrase for the item they want, such as "vintage graphic tee" or "black denim jacket". This should be matched against listing fields like title,description, category, and style_tags.
- `size` (str or None): The clothing size requested by the user, such as "S", "M", "L", or "XL". If size is None, the tool should not filter by size.
- `max_price` (float or None): The highest price the user is willing to pay. If max_price is provided, the tool should only return listings where price <= max_price. If max_price is None, the tool should not filter by price.

**What it returns:**
The tool returns a list of matching listing dictionaries from data/listings.json, sorted with the most relevant matches first. Each result should contain the listing's original fields, including id, title, description, category, style_tags, size, condition, price, colors, brand, and platform. The agent will use the first item in this list as the selected item for the next tool call.

**What happens if it fails or returns nothing:**
If no listings match the user's description, size, and max price, the tool returns an empty list [] instead of raising an exception. The agent should not call suggest_outfit or create_fit_card with empty search results. Instead, the agent should store an error message in session state and tell the user that no listings were found, then suggest adjusting the search description, increasing the budget, or loosening the size filter.

---

### Tool 2: suggest_outfit

**What it does:**
suggest_outfit takes the selected secondhand item and the user's wardrobe, then generates one or more outfit ideas that show how the new item could be worn. It should use the wardrobe items when available, but if the wardrobe is empty or minimal, it should still give useful general styling advice based on the new item's category, colors, and style tags.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): The selected listing dictionary returned by search_listings. It should include fields such as id, title, description, category, style_tags, size, condition, price, colors, brand, and platform.
- `wardrobe` (dict): The user's wardrobe data. This contains a list of wardrobe items that the agent can use to build an outfit around the selected new_item. Each wardrobe item may include fields such as item name, category, colors, style tags, and other clothing details depending on the wardrobe schema.

**What it returns:**
The tool returns a string containing a complete outfit suggestion. The suggestion should mention the selected new item and describe what to pair it with, using specific wardrobe pieces when possible. If the wardrobe has enough items, the output should include a complete look, such as a top, bottom, shoes, and optional accessories or styling notes.

**What happens if it fails or returns nothing:**
If the wardrobe is empty or too minimal, the tool should not crash or return an empty string. Instead, it should return a helpful general outfit suggestion using the new item's available details, such as its category, colors, style tags, and overall vibe. If the LLM call fails or no outfit can be generated, the agent should store an error message in session state and tell the user that it could not create a complete outfit, while suggesting that they add more wardrobe details or try a different item.

---

### Tool 3: create_fit_card

**What it does:**
create_fit_card takes the outfit suggestion and selected secondhand item, then turns them into a short, shareable fit card description. The output should sound like a social media caption or outfit post, not a plain product description.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): The outfit suggestion returned by suggest_outfit. This should describe how the selected item can be styled, including any wardrobe pieces, colors, vibe, or styling notes.
- `new_item`  (dict): The selected listing dictionary originally returned by search_listings. It should include fields such as title, price, platform, condition, brand, colors, category, and style_tags so the fit card can mention the thrifted item accurately.

**What it returns:**
The tool returns a short string containing a shareable fit card or caption-style description of the outfit. The fit card should mention the selected item and communicate the overall style or vibe of the outfit. Different inputs should produce different fit cards, and repeated runs should have some variation so the output does not feel copied or hardcoded.

**What happens if it fails or returns nothing:**
If the outfit string is empty, missing, or too incomplete to turn into a fit card, the tool should return a clear error message string instead of raising an exception. The agent should store that message in session state and tell the user that a fit card could not be created because the outfit suggestion was incomplete. If the LLM call fails, the tool should return a fallback caption using basic details from new_item, such as the item title, price, platform, and style tags.

---

### Additional Tools (if any)

### Additional Tool 1: compare_price

**What it does:**
`compare_price` checks whether the selected listing's price seems fair by comparing it against similar listings in the mock dataset.

**Input parameters:**
- `item` (dict): The selected listing returned by `search_listings`.
- `listings` (list): The full list of listing dictionaries from `data/listings.json`.

**What it returns:**
The tool returns a dictionary with the selected item's price, the average price of comparable listings, the number of comparable listings found, and a short verdict such as `"good deal"`, `"fair price"`, or `"overpriced"`.

**What happens if it fails or returns nothing:**
If there are not enough comparable listings, the tool should return a message saying there is not enough data to judge the price instead of crashing.

### Additional Tool 2: style_profile_memory

**What it does:**
`style_profile_memory` saves and loads the user's style preferences so the agent can reuse them across sessions. This lets the user avoid re-entering the same wardrobe preferences every time.

**Input parameters:**
- `user_preferences` (dict): A dictionary of style preferences, such as favorite colors, preferred fits, disliked items, common wardrobe pieces, and favorite styles.
- `mode` (str): Either `"save"` to store preferences or `"load"` to retrieve existing preferences.

**What it returns:**
The tool returns a dictionary containing the saved or loaded style profile. The profile may include fields like `favorite_colors`, `preferred_fit`, `style_tags`, `wardrobe_notes`, and `avoid`.

**What happens if it fails or returns nothing:**
If no saved profile exists, the tool should return an empty profile template and tell the agent to continue using the wardrobe information from the current query.

### Additional Tool 3: check_trends

**What it does:**
`check_trends` checks current or mock fashion trend information and returns style ideas that may match the user's requested item, size range, or style tags.

**Input parameters:**
- `description` (str): The item or style the user is searching for.
- `size` (str or None): The user's requested size, if provided.
- `style_tags` (list): Style tags from the selected listing or user preference profile.

**What it returns:**
The tool returns a list of trend notes or style ideas. Each trend result should include a trend name, matching style tags, and a short explanation of how it relates to the selected item.

**What happens if it fails or returns nothing:**
If no trend information is available, the tool should return an empty list or a short message saying no trend data was found. The agent should still continue with the normal outfit suggestion and fit card workflow.

---

## Planning Loop

**How does your agent decide which tool to call next?**
The agent starts by reading the user's query and extracting the item description, size, max price, and any wardrobe/style notes the user included. It then calls search_listings(description, size, max_price) first because the rest of the workflow depends on finding a valid secondhand item.

After search_listings runs, the planning loop checks whether the returned results list is empty. If results == [], the agent stores an error message in session["error"] and does not call suggest_outfit or create_fit_card, because there is no selected item to style. If stretch retry logic is enabled, the agent will retry the search one time with loosened constraints, such as setting size=None or removing the max price filter, and it will tell the user what was adjusted.

If search_listings returns one or more listings, the agent selects the first result as the best match and stores it as session["selected_item"] = results[0]. The agent then calls suggest_outfit(new_item=session["selected_item"], wardrobe=wardrobe) to create an outfit suggestion using the selected listing and the user's wardrobe.

After suggest_outfit runs, the agent checks whether the outfit suggestion is missing, empty, or an error message. If the outfit suggestion is usable, it stores it as session["outfit_suggestion"] and then calls create_fit_card(outfit=session["outfit_suggestion"], new_item=session["selected_item"]). If the outfit suggestion fails, the agent stores an error message in session["error"] and stops before creating a fit card.

After create_fit_card runs, the agent stores the final result as session["fit_card"]. The loop is complete when the session contains either a final fit card or an error message explaining why the workflow stopped.

---

## State Management

**How does information from one tool get passed to the next?**
The agent uses a session dictionary to store information during one complete user interaction. Each tool reads from and writes to this session so the user does not have to repeat information between steps.

The session tracks the original user query, extracted search inputs, search results, selected item, wardrobe data, outfit suggestion, fit card, and any error message. After search_listings returns results, the agent stores the full results list in session["search_results"] and stores the top result in session["selected_item"]. That selected item is then passed directly into suggest_outfit.

After suggest_outfit returns an outfit suggestion, the agent stores it in session["outfit_suggestion"]. The agent then passes both session["outfit_suggestion"] and session["selected_item"] into create_fit_card. If any step fails, the session stores the problem in session["error"], and later tools are skipped when their required input is missing.

Example session keys:

session["query"]: the user's original request
session["description"]: the extracted item description
session["size"]: the requested size or None
session["max_price"]: the requested max price or None
session["wardrobe"]: the user's wardrobe or example wardrobe
session["search_results"]: list of matching listings
session["selected_item"]: the listing chosen for styling
session["outfit_suggestion"]: the outfit returned by suggest_outfit
session["fit_card"]: the final caption-style output
session["error"]: an error message if the workflow stops early

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Return an empty list [], store "No listings found for that search." in session["error"], and do not call suggest_outfit or create_fit_card. The agent tells the user: "I couldn't find any listings that matched your item, size, and budget. Try using a broader description, removing the size filter, or increasing your max price." |
| suggest_outfit | Wardrobe is empty | Continue without crashing and generate a general outfit suggestion using the selected item's category, colors, style tags, and vibe. The agent tells the user: "I don't have saved wardrobe items to match this with yet, so I'll style it with general pieces that fit the item's vibe. Add wardrobe details later for a more personalized outfit."|
| create_fit_card | Outfit input is missing or incomplete | Return a clear error message string, store "Fit card could not be created because the outfit suggestion was missing or incomplete." in session["error"], and leave session["fit_card"] as None. The agent tells the user: "I couldn't create a fit card because the outfit suggestion was incomplete. Try generating the outfit again or choose another listing." |

---

## Architecture

```mermaid
flowchart TD
    A[User query] --> B[Planning Loop]

    B --> C[Extract description, size, max_price, and wardrobe notes]
    C --> D[Tool 1: search_listings(description, size, max_price)]

    D --> E{Did search_listings return results?}

    E -- No: results == [] --> F[Store error in session["error"]]
    F --> G[Return message: No listings found. Try changing description, size, or budget.]
    G --> Z[Return session]

    E -- Yes: results found --> H[Store session["search_results"] = results]
    H --> I[Store session["selected_item"] = results[0]]

    I --> J[Tool 2: suggest_outfit(selected_item, wardrobe)]
    J --> K{Is outfit suggestion usable?}

    K -- No: empty or error --> L[Store error in session["error"]]
    L --> M[Return message: Could not create outfit suggestion.]
    M --> Z

    K -- Yes --> N[Store session["outfit_suggestion"] = outfit_suggestion]

    N --> O[Tool 3: create_fit_card(outfit_suggestion, selected_item)]
    O --> P{Was fit card created?}

    P -- No: missing or incomplete outfit --> Q[Store error in session["error"]]
    Q --> R[Set session["fit_card"] = None]
    R --> S[Return message: Fit card could not be created.]
    S --> Z

    P -- Yes --> T[Store session["fit_card"] = fit_card]
    T --> U[Return selected item, outfit suggestion, and fit card]
    U --> Z

    subgraph Session State
        SS1[query]
        SS2[description / size / max_price]
        SS3[wardrobe]
        SS4[search_results]
        SS5[selected_item]
        SS6[outfit_suggestion]
        SS7[fit_card]
        SS8[error]
    end

    C -. writes .-> SS1
    C -. writes .-> SS2
    C -. writes/reads .-> SS3
    H -. writes .-> SS4
    I -. writes .-> SS5
    J -. reads .-> SS5
    J -. reads .-> SS3
    N -. writes .-> SS6
    O -. reads .-> SS6
    O -. reads .-> SS5
    T -. writes .-> SS7
    F -. writes .-> SS8
    L -. writes .-> SS8
    Q -. writes .-> SS8
```

---

## AI Tool Plan

 **Milestone 2 planning** 
 I will use ChatGPT to help turn the project requirements into specific implementation-ready descriptions. I will give ChatGPT the required tool sections from planning.md, the project requirements, and my understanding of the listings and wardrobe data. I expect it to help me write clear specs for each tool, the planning loop, state management, error handling, and the architecture diagram. I will verify the output by checking that each section names exact function parameters, return values, failure behavior, and matches the starter code function signatures.

 **Milestone 3 tool implementation**
  I will use Claude to help implement one tool at a time in tools.py. For search_listings, I will give Claude the Tool 1 spec from planning.md and ask it to implement search_listings(description, size, max_price) using load_listings() from utils/data_loader.py. Before trusting the code, I will check that it filters by description, optional size, and optional max price, returns a list of listing dictionaries, and returns [] when there are no matches. I will verify it by running multiple direct test queries, including one query that should return results and one impossible query that should return an empty list.

For suggest_outfit, I will give Claude the Tool 2 spec, the wardrobe schema, and the requirement that it use Groq llama-3.3-70b-versatile. I expect Claude to produce a function that accepts new_item and wardrobe, creates a prompt for the LLM, and handles an empty wardrobe without crashing. I will verify it by calling the function with get_example_wardrobe() and get_empty_wardrobe() and checking that both return useful strings.

For create_fit_card, I will give Claude the Tool 3 spec and the actual function signature from tools.py. I expect it to produce a function that accepts outfit and new_item, calls the LLM, and returns a short caption-style fit card. I will verify that it handles an empty outfit string by returning a clear error message instead of raising an exception, and I will run it more than once to confirm the output has some variation.

 **Milestone 4 planning loop implementation**
  I will give Claude the ## Planning Loop, ## State Management, ## Error Handling, and ## Architecture sections from planning.md. I expect it to implement run_agent() in agent.py so that the agent branches based on previous results instead of calling every tool unconditionally. I will verify that the code checks whether search_listings returned an empty list before calling suggest_outfit, stores selected_item, outfit_suggestion, fit_card, and error in the session dictionary, and returns early when required data is missing.

For Milestone 4 app wiring, I will use Claude or Copilot to help implement handle_query() in app.py. I will give it the run_agent() return structure and the Gradio output panel requirements. I expect it to map the selected item, outfit suggestion, fit card, and error message from the session dictionary into the interface outputs. I will verify it by running python app.py and checking that the UI updates correctly for both a successful query and a no-results query.

 **Milestone 5 testing** 
 I will use ChatGPT to help design pytest cases and terminal commands that deliberately trigger each failure mode. I will give it the ## Error Handling table and the tool specs from planning.md. I expect it to produce tests for no search results, empty wardrobe, and missing outfit input. I will verify by running pytest tests/ and confirming every required failure mode returns an informative response instead of crashing.

 **Milestone 6 documentation**
  I will use ChatGPT to help organize the README after the code is working. I will give it my final planning.md, notes from testing, and examples of successful and failed runs. I expect it to help draft the tool inventory, planning loop explanation, state management description, error handling examples, spec reflection, and AI usage section. I will verify the README by checking that every documented function name, parameter, and return value matches the actual code before submitting.

 **Stretch Features**
  I will update planning.md before implementing each stretch feature. I will use Claude to help implement the price comparison tool, style profile memory, trend awareness, and retry logic with fallback one at a time. I will verify each stretch feature separately before connecting it into the agent loop, and I will confirm that the required three-tool workflow still works after each stretch feature is added.

---

## A Complete Interaction (Step by Step)

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
The agent reads the user query and extracts the search inputs:

description = "vintage graphic tee"
size = None because the user did not give a size
max_price = 30.0
wardrobe/style notes = "baggy jeans and chunky sneakers"

The agent calls:
search_listings(description="vintage graphic tee", size=None, max_price=30.0)

The tool searches the mock listings dataset using the description, does not filter by size, and only keeps items with price <= 30.0.

**Step 2:**
search_listings returns a non-empty list of matching listing dictionaries. For example, it may return a result like:

{"id": "example_id", "title": "Faded Band Tee", "description": "Vintage-style graphic band tee with a worn-in look.", "category": "tops", "style_tags": ["vintage", "graphic", "grunge"], "size": "M", "condition": "Good", "price": 22.0, "colors": ["black", "gray"], "brand": "Unknown", "platform": "Depop"}

Because the results list is not empty, the agent stores:

session["search_results"] = results
session["selected_item"] = results[0]

The agent then calls:
suggest_outfit(new_item=session["selected_item"], wardrobe=wardrobe)

The wardrobe passed into this tool includes the user's stated style notes, especially that they mostly wear baggy jeans and chunky sneakers.

**Step 3:**
suggest_outfit returns a usable outfit suggestion string. For example:

"Style the faded band tee with your baggy jeans and chunky sneakers for a relaxed 90s-inspired look. Keep the tee slightly oversized, cuff the sleeves once, and add a simple silver chain or black hoodie if you want more of a grunge layer."

The agent stores:

session["outfit_suggestion"] = outfit_suggestion

Because the outfit suggestion is not empty, the agent calls:
create_fit_card(outfit=session["outfit_suggestion"], new_item=session["selected_item"])

**Step 4:**
create_fit_card returns a short caption-style fit card. For example:

"thrifted a faded band tee for $22 and paired it with baggy denim + chunky sneakers — easy 90s grunge energy without trying too hard."

The agent stores:

session["fit_card"] = fit_card

The workflow is now complete because the session contains a selected item, an outfit suggestion, and a final fit card.

**Final output to user:**
The user sees the selected listing, the outfit suggestion, and the fit card.

Selected item:
Faded Band Tee — $22 on Depop, Good condition

Outfit suggestion:
Style the faded band tee with baggy jeans and chunky sneakers for a relaxed 90s-inspired look. Cuff the sleeves once and add a silver chain or hoodie if you want more of a grunge layer.

Fit card:
thrifted a faded band tee for $22 and paired it with baggy denim + chunky sneakers — easy 90s grunge energy without trying too hard.
