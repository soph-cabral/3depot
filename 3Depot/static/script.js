// Wait for the DOM to be fully loaded before running the script
document.addEventListener('DOMContentLoaded', function() {

  // Add a click event listener to the 'aboutButton'
  document.getElementById('upload').addEventListener('click', function() {
      // Redirect to the 'about.html' page when 'aboutButton' is clicked
      window.location.href = 'upload.html';
  });

  // Add a click event listener to the 'contributorsButton'
  document.getElementById('mydepot').addEventListener('click', function() {
      // Redirect to the 'contributors.html' page when 'contributorsButton' is clicked
      window.location.href = 'mydepot.html';
  });

  // Add a click event listener to the 'processButton'
  document.getElementById('logout').addEventListener('click', function() {
      // Redirect to the 'process.html' page when 'processButton' is clicked
      window.location.href = 'logout.html';
  });
});
