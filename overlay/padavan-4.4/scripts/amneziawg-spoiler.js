function spoiler_toggle(element){
    if (document.getElementById(element).style.display == "none") {
        document.getElementById(element).style.display = "";
    } else {
        document.getElementById(element).style.display = "none";
    }
}
