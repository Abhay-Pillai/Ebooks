from flask import Flask, render_template_string

app = Flask(__name__)

template = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Book Opening Animation</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400..700;1,400..700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">

  <style>
    :root {
      --book-width: 400px;
      --book-height: 550px;
      --cover-color: #1e63b8;
      --page-color: #fdfaf3;
      --text-color: #333;
      --accent-color: #a0522d;
    }

    html, body {
      margin: 0;
      padding: 0;
      height: 100%;
      display: flex;
      justify-content: center;
      align-items: center;
      background: #e0d8c7; /* A soft, warm background */
      font-family: 'Lora', serif;
      perspective: 1500px;
    }

    .book-container {
      width: var(--book-width);
      height: var(--book-height);
      position: relative;
      transform-style: preserve-3d;
      transition: transform 1.8s linear;
    }
    
    .book-container.opened {
      transform: translateX(calc(var(--book-width) / 2));
    }

    .book-cover {
      position: absolute;
      width: 100%;
      height: 100%;
      transform-origin: left center;
      transition: transform 1.8s linear;
      z-index: 10;
      transform-style: preserve-3d;
    }
    
    .book-cover.opened {
      transform: rotateY(-180deg);
    }

    .cover-front, .cover-back {
      position: absolute;
      width: 100%;
      height: 100%;
      top: 0;
      left: 0;
      backface-visibility: hidden;
      border-radius: 5px 15px 15px 5px;
      display: flex;
      justify-content: center;
      align-items: center;
      text-align: center;
      padding: 20px;
      box-sizing: border-box;
    }

    .cover-front {
      background: var(--cover-color);
      color: white;
      font-family: 'Playfair Display', serif;
      font-size: 2.5rem;
      box-shadow: 
        inset 4px 0 10px -4px rgba(0,0,0,0.5),
        5px 5px 20px rgba(0,0,0,0.4);
    }

    .cover-back {
      background: var(--cover-color);
      transform: rotateY(180deg);
      box-shadow: inset -4px 0 10px -4px rgba(0,0,0,0.5);
    }

    /* This is the single page that will flip */
    .flipping-page {
        position: absolute;
        top: 2px;
        left: 2px;
        width: calc(100% - 2px);
        height: calc(100% - 4px);
        transform-origin: left center;
        transition: transform 1.2s linear; /* Faster page flip */
        transform-style: preserve-3d;
    }

    /* Stacking the pages */
    #page1 { z-index: 8; }
    #page2 { z-index: 7; }
    #page3 { z-index: 6; }

    .flipping-page.flipped {
        transform: rotateY(-180deg);
    }
    
    .page-face {
        position: absolute;
        width: 100%;
        height: 100%;
        top: 0;
        backface-visibility: hidden;
        background: var(--page-color);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 40px;
        box-sizing: border-box;
        border-radius: 5px;
    }

    .page-front {
        right: 0;
    }
    
    .page-back {
        left: 0;
        transform: rotateY(180deg);
    }


    /* These are the static pages underneath it all */
    .book-pages {
      position: absolute;
      width: 100%;
      height: 100%;
      top: 0;
      left: 0;
      display: flex;
      box-shadow: 10px 10px 25px rgba(0,0,0,0.3);
      border-radius: 5px;
      z-index: 5;
    }

    .page {
      height: 100%;
      background: var(--page-color);
      color: var(--text-color);
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      box-sizing: border-box;
      padding: 40px;
      text-align: center;
    }

    .page#static-right-page {
      width: 100%;
      border-radius: 5px;
      padding-left: 50%;
    }
    
    .page-back h1 {
        font-family: 'Playfair Display', serif;
        font-size: 2.2rem;
        margin: 0;
        color: var(--accent-color);
        line-height: 1.3;
        text-align: center;
    }

    .page p {
        font-size: 1.2rem;
        font-style: italic;
        margin: 0;
        line-height: 1.6;
    }

  </style>
</head>
<body>

  <div class="book-container">
    <div class="book-cover" id="book-cover">
      <div class="cover-front">
        E-Books Website
      </div>
      <div class="cover-back"></div>
    </div>

    <!-- Multiple flipping pages -->
    <div class="flipping-page" id="page1">
      <div class="page-face page-front"></div>
      <div class="page-face page-back"></div>
    </div>
    <div class="flipping-page" id="page2">
      <div class="page-face page-front"></div>
      <div class="page-face page-back"></div>
    </div>
    <div class="flipping-page" id="page3">
      <div class="page-face page-front"></div>
      <div class="page-face page-back">
        <h1>Welcome to<br>Encore Library</h1>
      </div>
    </div>

    <div class="book-pages">
      <div class="page" id="static-right-page">
        <p>"Where your story awaits."</p>
      </div>
    </div>
  </div>

  <script>
    document.addEventListener('DOMContentLoaded', () => {
      const bookContainer = document.querySelector('.book-container');
      const bookCover = document.getElementById('book-cover');
      const pages = document.querySelectorAll('.flipping-page');
      
      // Open the book cover first
      setTimeout(() => {
        bookCover.classList.add('opened');
        bookContainer.classList.add('opened');
      }, 500);

      // Flip each page in sequence
      pages.forEach((page, index) => {
        setTimeout(() => {
          page.classList.add('flipped');
          // Ensure the flipped page is on top
          page.style.zIndex = 11 + index; 
        }, 1000 + (index * 500)); // Stagger the flip of each page
      });
      setTimeout(() => {
      window.location.href = "/login";
      }, 4000); // adjust timing if needed
    });

    
  </script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(template)

if __name__ == "__main__":
    app.run(debug=True)

