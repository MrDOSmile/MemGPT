def ask_question(question, category, responses):
    response = input(f"{question} ({category}): ")
    responses.append(f"{category}: {question}: {response}\n")

def main():
    responses = []

    # Personal Information
    ask_question("Name", "Personal Information", responses)
    ask_question("Birthday", "Personal Information", responses)
    ask_question("Gender", "Personal Information", responses)
    ask_question("Nationality", "Personal Information", responses)

    # Location
    ask_question("Current City or Region", "Location", responses)

    # Occupation and Education
    ask_question("Current Job/Profession", "Occupation and Education", responses)

    # Hobbies and Interests
    ask_question("What are your favorite hobbies or leisure activities?", "Hobbies and Interests", responses)

    # Favorite Books, Movies, and Music
    ask_question("Share some of your favorite books, movies, or music artists.", "Favorite Books, Movies, and Music", responses)

    # Travel and Adventure
    ask_question("Have you traveled to any exciting destinations recently?", "Travel and Adventure", responses)

    # Food and Dining
    ask_question("What's your favorite cuisine or dish?", "Food and Dining", responses)

    # Life Goals and Ambitions
    ask_question("What are some of your short-term and long-term life goals?", "Life Goals and Ambitions", responses)

    # Personality and Values
    ask_question("How would you describe your personality in a few words?", "Personality and Values", responses)

    # Social and Volunteering
    ask_question("What social causes are important to you?", "Social and Volunteering", responses)

    # Relationship Preferences
    ask_question("Are you looking for friendship, dating, or networking?", "Relationship Preferences", responses)

    # Save responses to a text file
    name = input("What's your name? : ")
    with open(f"X:\AI\MemGPT\MemGPT\MemGPT\memgpt\humans\examples\{name}.txt", "w") as file:
        for response in responses:
            file.write(response)

    print(f"Responses have been saved to 'X:\AI\MemGPT\MemGPT\MemGPT\memgpt\humans\examples\{name}.txt'.")

if __name__ == '__main__':
    main()
