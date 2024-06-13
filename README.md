# ScrapEmailFromWeb
Este código es capaz de realizar una búsqueda en Google e intentar extraer el email de contacto de las webs resultantes usando Selenium.

## Instalación
Se ha creado un archivo ejecutable como release para que sea más sencillo de usar. Sólo es necesario bajarlo y ejecutarlo.

Se abrirá una consola que permite al usuario escribir lo que desee buscar en Google para obtener los emails.

El código contine una serie de palabras clave para filtrar las URLs resultantes de la búsqueda de Google. Esta lista no es fija y se puede ampliar en cualquier momento o usar otra propia.

La salida del programa consiste en un fichero CSV `resultado.csv` que se creará en la raíz de donde se ejecute el programa. Este fichero se puede abrir con Excel sin ningún problema, aunque quizá sea necesario especificar el separador `;`.

### Errores comunes
Se ha hecho una estimación del número de resultados que se pide a Google sin que detecte que es un bot el que está haciendo peticiones. Ese número oscila entre 250 y 350 peticiones, pero cabe la posibilidad de que nos devuleva un error `429`, por lo que habrá que esperar hasta que vuelva a autorizar las búsquedas desde nuestra IP.

Es posible que si se clica en el link del error (consola) y se haga el Captcha nos permita hacer otra búsqueda.