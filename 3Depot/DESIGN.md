# Design

This section details the technologies used in the development of 3Depot and their specific roles in the project.

## Python
- Python serves as the core programming language for the website, handling dynamic user input and output.
- It is crucial for the backend management system, including tasks like user registration, model management, and storing models in specific backend directories.

## JavaScript
- JavaScript is employed to enhance the interactivity of the website.
- It is used for client-side scripting to make the web pages interactive and responsive to user actions.
- JavaScript allows for visual error handling, by displaying explanatory text to users that guides them on the use of the text fields.

## HTML
- HTML is used to structure the web pages on the site.
- It provides the basic layout and framework upon which CSS and JavaScript add styling and functionality.
- Jinja is used to extend an html template and bootstrap is integrated for a uniform and visually pleasing interfase.

## CSS
- CSS is utilized for styling the web pages.
- It enhances the visual appeal of the site, ensuring a user-friendly and engaging interface.
- Photos, paragraphs, headers, forms, model-viwers, and other html tags are structured using CSS.

## SQL (SQLite3)
- SQLite3, a lightweight SQL database, is used for data storage.
- The `users` table stores user information and is linked to user sessions for maintaining state and authentication.
- The `models` table stores information about each 3D model, including unique paths to the stored models.
