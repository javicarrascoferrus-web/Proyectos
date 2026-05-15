window.JocarsaWysiwyg = (function(){

    function crearEditor(textarea){

        let contenedor = document.createElement("div")
        contenedor.className = "jocarsa-wysiwyg-contenedor"

        let barra = document.createElement("div")
        barra.className = "jocarsa-wysiwyg-barra"

        let botonBold = document.createElement("button")
        botonBold.innerHTML = "<b>B</b>"

        let botonItalic = document.createElement("button")
        botonItalic.innerHTML = "<i>I</i>"

        barra.appendChild(botonBold)
        barra.appendChild(botonItalic)

        let editor = document.createElement("div")
        editor.className = "jocarsa-wysiwyg-editor"
        editor.contentEditable = true

        editor.innerHTML = textarea.value

        textarea.classList.add("jocarsa-wysiwyg-textarea-oculto")

        textarea.parentNode.insertBefore(contenedor, textarea)
        contenedor.appendChild(textarea)
        contenedor.appendChild(barra)
        contenedor.appendChild(editor)

        function sincronizar(){
            textarea.value = editor.innerHTML
        }

        botonBold.onclick = function(){
            document.execCommand("bold")
            sincronizar()
        }

        botonItalic.onclick = function(){
            document.execCommand("italic")
            sincronizar()
        }

        editor.addEventListener("input", sincronizar)
    }

    function init(){
        let areas = document.querySelectorAll(".jocarsa-wysiwyg")

        areas.forEach(function(textarea){
            crearEditor(textarea)
        })
    }

    document.addEventListener("DOMContentLoaded", init)

    return {
        init:init
    }

})()
