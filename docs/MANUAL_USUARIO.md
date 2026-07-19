# SIRCCD

## Manual de Usuario

**Sistema Inteligente Urbano para Reporte y Priorización de Daños Viales**

Versión: 1.0
Fecha: julio 2026
Autores: Equipo SIRCCD

---

## Tabla de contenido

1. [Introducción](#1-introducción)
2. [Requisitos](#2-requisitos)
3. [Tipos de usuario](#3-tipos-de-usuario)
4. [Acceso al sistema](#4-acceso-al-sistema)
5. [Aplicación móvil](#5-aplicación-móvil)
6. [Plataforma web](#6-plataforma-web)
7. [Explicación de la información mostrada](#7-explicación-de-la-información-mostrada)
8. [Preguntas frecuentes](#8-preguntas-frecuentes)
9. [Solución de problemas](#9-solución-de-problemas)
10. [Buenas prácticas](#10-buenas-prácticas)
11. [Glosario](#11-glosario)

---

## 1. Introducción

### Propósito del sistema

SIRCCD es una plataforma que permite a los ciudadanos reportar daños en la vía pública —baches y grietas— mediante una fotografía tomada desde su teléfono. El sistema analiza automáticamente cada fotografía con visión computacional para clasificar el tipo de daño y su severidad, agrupa los reportes que corresponden al mismo daño físico y calcula una prioridad de atención. El personal municipal utiliza una plataforma web para revisar, dar seguimiento y cerrar estos incidentes, respetando tiempos de respuesta (SLA) definidos por la institución.

### Objetivo del manual

Explicar, paso a paso, el uso de las dos aplicaciones que componen SIRCCD —la aplicación móvil ciudadana y la plataforma web administrativa— de forma que cualquier persona pueda aprender a operar el sistema únicamente leyendo este documento.

### Alcance

Este manual cubre las funcionalidades disponibles en la versión actual del sistema: registro e inicio de sesión, creación y consulta de reportes desde la aplicación móvil, y gestión de incidentes, usuarios, SLA y configuración de prioridad desde la plataforma web. No cubre procedimientos de instalación, despliegue ni configuración de servidores, los cuales se documentan por separado para el equipo técnico.

### Público objetivo

- Ciudadanos que desean reportar daños viales en su comunidad.
- Supervisores municipales encargados de dar seguimiento a los incidentes.
- Administradores del sistema encargados de la configuración y gestión de usuarios.

---

## 2. Requisitos

### Plataforma web

| Requisito | Detalle |
|---|---|
| Navegador compatible | Versión reciente de Chrome, Firefox, Edge o Safari |
| Conexión | Acceso a internet estable |
| Resolución recomendada | 1280×720 o superior (la interfaz también se adapta a pantallas más pequeñas) |

### Aplicación móvil

| Requisito | Detalle |
|---|---|
| Sistema operativo | Android o iOS |
| Permisos necesarios | Cámara y ubicación (obligatorios para reportar un daño); acceso a galería de imágenes |
| Conexión | Internet para iniciar sesión, sincronizar y consultar reportes. La captura de un reporte puede realizarse sin conexión y se sincroniza automáticamente al recuperar la señal |

---

## 3. Tipos de usuario

SIRCCD define tres roles. Cada usuario tiene uno solo.

| Rol | Descripción | Acceso |
|---|---|---|
| **Ciudadano** | Persona que reporta daños viales y da seguimiento a sus propios reportes | Aplicación móvil y portal ciudadano de la plataforma web |
| **Supervisor** | Personal municipal que revisa incidentes, actualiza su estado y gestiona el cumplimiento de SLA | Panel administrativo de la plataforma web |
| **Administrador** | Además de las funciones de supervisor, gestiona usuarios del sistema y la configuración del algoritmo de priorización | Panel administrativo de la plataforma web, incluidas las secciones de Usuarios y Configuración |

> **Nota:** todo usuario que se registra desde la aplicación móvil o el formulario público de registro queda creado con el rol Ciudadano. Los roles de Supervisor y Administrador se asignan desde la sección **Usuarios** del panel web por un Administrador existente.

---

## 4. Acceso al sistema

El acceso es común a la aplicación móvil y a la plataforma web: ambas utilizan la misma cuenta.

### 4.1 Registro

**Objetivo:** crear una cuenta nueva en el sistema.

**Pasos:**

1. En la pantalla de inicio de sesión, seleccionar la opción **Registrarse**.
2. Completar los campos: nombre de usuario, correo electrónico, nombre completo y contraseña.
3. Confirmar la contraseña.
4. Presionar **Crear cuenta**.

**Resultado esperado:** el sistema muestra un mensaje de registro exitoso y redirige a la pantalla de inicio de sesión.

[Captura: Formulario de registro]

> **Nota:** si las contraseñas ingresadas no coinciden, el sistema no permite continuar y muestra un aviso.

### 4.2 Inicio de sesión

**Objetivo:** acceder al sistema con una cuenta existente.

**Pasos:**

1. Ingresar nombre de usuario y contraseña.
2. Presionar **Iniciar sesión**.

**Resultado esperado:** el sistema dirige automáticamente al usuario según su rol: el ciudadano llega a su portal de reportes, y el supervisor o administrador llega al panel administrativo.

[Captura: Pantalla de inicio de sesión]

> **Advertencia:** si las credenciales son incorrectas, el sistema muestra un mensaje de error y no concede acceso.

### 4.3 Cerrar sesión

**Objetivo:** finalizar la sesión activa de forma segura.

**Pasos:**

1. Presionar el ícono de cierre de sesión, ubicado en la barra superior (plataforma web) o en el perfil (aplicación móvil).

**Resultado esperado:** el sistema cierra la sesión y regresa a la pantalla de inicio de sesión.

---

## 5. Aplicación móvil

La aplicación móvil está dirigida a ciudadanos. Permite reportar daños viales y consultar el estado de los reportes propios.

### 5.1 Permisos iniciales

Al primer inicio de sesión, la aplicación solicita permisos de cámara y ubicación, explicando para qué se utilizan. Ambos permisos son necesarios para poder crear un reporte.

[Captura: Pantalla de solicitud de permisos]

### 5.2 Crear un reporte

**Objetivo:** reportar un daño vial detectado por el ciudadano.

**Pasos:**

1. Desde la pantalla principal, presionar el botón para reportar un nuevo daño.
2. Tomar una fotografía del bache o grieta con la cámara del dispositivo, o seleccionar una imagen desde la galería.
3. La aplicación captura automáticamente la ubicación GPS del dispositivo y sugiere una dirección aproximada (calle, ciudad, provincia); esta dirección puede editarse manualmente.
4. Escribir una descripción del daño (opcional).
5. Presionar **Enviar reporte**.

**Resultado esperado:** el reporte queda registrado. Si el dispositivo tiene conexión a internet, se envía de inmediato al servidor; si no la tiene, el reporte se guarda como pendiente en el dispositivo y se envía automáticamente cuando se recupera la conexión.

[Captura: Formulario de creación de reporte con foto y ubicación]

> **Nota:** los reportes pendientes de sincronización se identifican con un aviso en la parte superior de la pantalla de reportes, indicando cuántos están en espera de envío.

> **Importante:** una vez enviado, el reporte no puede editarse ni eliminarse desde la aplicación. Si el reporte fue creado por error o está duplicado, el personal municipal lo identificará durante la revisión.

### 5.3 Consultar mis reportes

**Objetivo:** ver el estado de los reportes enviados.

**Pasos:**

1. Ingresar a la sección de reportes o al historial de reportes.
2. Consultar la lista de reportes propios, cada uno con su tipo de daño, severidad y estado actual.
3. Seleccionar un reporte para ver su detalle: fotografía, ubicación, descripción y estado.

**Resultado esperado:** el ciudadano visualiza el progreso de cada reporte enviado.

[Captura: Historial de reportes del ciudadano]

[Captura: Detalle de un reporte]

### 5.4 Perfil

**Objetivo:** consultar los datos de la cuenta.

**Pasos:**

1. Ingresar a la sección de perfil desde el menú principal.

**Resultado esperado:** se muestra la información básica del usuario autenticado.

[Captura: Pantalla de perfil]

---

## 6. Plataforma web

La plataforma web tiene dos vistas según el rol: el **portal ciudadano** (rol Ciudadano) y el **panel administrativo** (roles Supervisor y Administrador).

### 6.1 Portal ciudadano

Al iniciar sesión, un ciudadano llega a su portal, donde puede:

- Ver un resumen de sus reportes (total, en proceso, aprobados, rechazados).
- Crear un nuevo reporte con foto, ubicación y descripción, de forma equivalente a la aplicación móvil.
- Consultar la lista de sus reportes con su estado individual.
- Ver un mapa con la ubicación de todos sus reportes.

[Captura: Portal ciudadano — resumen y mapa]

### 6.2 Panel administrativo — Dashboard

Es la pantalla principal para Supervisor y Administrador. Muestra un resumen general del estado de los incidentes y reportes del sistema.

[Captura: Dashboard principal]

### 6.3 Incidentes

**Objetivo:** revisar y dar seguimiento a los incidentes generados a partir de los reportes ciudadanos.

**Descripción:** un incidente agrupa uno o varios reportes que corresponden al mismo daño físico. La sección de incidentes ofrece tres formas de visualización: tabla, mapa, o ambas divididas en pantalla.

**Procedimiento:**

1. Ingresar a **Incidentes** desde el menú lateral.
2. Aplicar filtros por severidad, score de prioridad, estado, rango de fechas o zona, según se necesite.
3. Alternar entre vista de tabla, mapa o vista combinada mediante los botones correspondientes.
4. Seleccionar un incidente para ver su detalle.
5. Exportar el listado filtrado, si se requiere, mediante el menú de exportación.

**Resultado esperado:** el usuario localiza los incidentes que necesita revisar, filtrados según el criterio elegido.

[Captura: Listado de incidentes en vista tabla]

[Captura: Listado de incidentes en vista mapa]

**Buena práctica:** combinar los filtros de severidad y estado para priorizar primero los incidentes de mayor gravedad que aún no han sido atendidos.

#### 6.3.1 Detalle de incidente

Al abrir un incidente se muestra:

- Fotografía del daño.
- Ubicación en un mapa.
- Tipo de daño, severidad, score y nivel de prioridad.
- Estado actual y su línea de tiempo (historial de cambios de estado).
- Indicador de cumplimiento de SLA.

[Captura: Detalle de un incidente]

**Cambio de estado** (solo Supervisor y Administrador):

1. Dentro del detalle del incidente, presionar el botón de actualizar estado.
2. Seleccionar el nuevo estado entre las transiciones permitidas para el estado actual.
3. Confirmar el cambio.

**Resultado esperado:** el estado del incidente se actualiza y queda registrado en la línea de tiempo del incidente.

[Captura: Modal de actualización de estado]

> Ver la lista completa de estados posibles en la sección [7. Explicación de la información mostrada](#7-explicación-de-la-información-mostrada).

### 6.4 Reportes

**Objetivo:** consultar los reportes individuales enviados por los ciudadanos y, cuando corresponda, registrar un reporte manualmente.

**Procedimiento:**

1. Ingresar a **Reportes** desde el menú lateral.
2. Consultar el listado de reportes recibidos.
3. Para registrar un reporte de forma manual, presionar **Crear Reporte** y completar el formulario (foto, ubicación, descripción).

[Captura: Listado de reportes]

[Captura: Formulario de creación manual de reporte]

### 6.5 SLA

**Objetivo:** monitorear el cumplimiento de los tiempos de respuesta y resolución establecidos para los incidentes.

**Descripción:** esta sección muestra estadísticas de incidentes según su relación con el SLA (a tiempo, próximos a vencer, vencidos) y permite consultar y ajustar la configuración del SLA.

[Captura: Panel de SLA]

> **Nota:** la edición de la configuración del SLA está disponible únicamente para el rol Administrador.

### 6.6 Usuarios

**Disponible para:** Supervisor y Administrador (la creación, edición y eliminación de cuentas requiere permisos administrativos).

**Objetivo:** gestionar las cuentas del personal y sus roles dentro del sistema.

**Procedimiento:**

1. Ingresar a **Usuarios** desde el menú lateral.
2. Buscar un usuario por nombre o correo, si es necesario.
3. Para crear un usuario, presionar **Nuevo usuario**, completar los datos y asignar un rol (Ciudadano, Supervisor o Administrador).
4. Para editar un usuario existente, presionar el ícono de edición sobre la fila correspondiente.
5. Para desactivar, reactivar o eliminar una cuenta, utilizar los íconos de acción correspondientes en la misma fila.

**Resultado esperado:** la cuenta queda creada, actualizada o desactivada según la acción realizada.

[Captura: Listado de usuarios]

[Captura: Formulario de creación de usuario]

### 6.7 Configuración

**Disponible para:** Administrador.

**Objetivo:** ajustar los parámetros del algoritmo que calcula la prioridad de los incidentes.

**Descripción:** desde esta sección se configuran los pesos que el sistema utiliza para calcular el score de prioridad (severidad, antigüedad, tipo de daño, ubicación y duplicados), así como parámetros de radio de proximidad a puntos de interés, radio y ventana de tiempo para detección de duplicados, y parámetros de agrupamiento de reportes.

**Procedimiento:**

1. Ingresar a **Configuración** desde el menú lateral.
2. Ajustar los valores necesarios mediante los controles disponibles.
3. Presionar **Guardar** para aplicar los cambios, o **Restablecer** para volver a los valores por defecto.

**Resultado esperado:** los nuevos parámetros se aplican al cálculo de prioridad de los incidentes.

[Captura: Panel de configuración de prioridad]

> **Advertencia:** modificar estos valores afecta el orden de prioridad de todos los incidentes del sistema. Se recomienda realizar cambios con conocimiento del impacto esperado.

### 6.8 Guía de uso integrada

La plataforma web incluye, además de este manual, una guía de uso resumida disponible dentro de la propia aplicación en la ruta **/guia**, accesible desde el ícono de ayuda en la barra superior del portal ciudadano y desde el menú lateral del panel administrativo.

---

## 7. Explicación de la información mostrada

| Elemento | Significado |
|---|---|
| **Tipo de daño** | Clasificación detectada automáticamente a partir de la fotografía: bache o grieta |
| **Severidad** | Nivel de gravedad del daño: Baja, Media o Alta |
| **Prioridad** | Nivel de atención sugerido para el incidente, calculado a partir de severidad, antigüedad, tipo de daño, ubicación y cantidad de reportes duplicados: Baja, Media, Alta o Crítica |
| **Score de prioridad** | Valor numérico que sustenta el nivel de prioridad asignado |
| **Estado del incidente** | Etapa del ciclo de vida del incidente: Reportado, Asignado, En Progreso, Completado, Verificado o Cerrado |
| **Estado del reporte** | Etapa de revisión de un reporte individual: Analizando, Pendiente, Aprobado o Rechazado |
| **SLA** | Indicador de si el incidente se encuentra dentro del tiempo de respuesta/resolución establecido, próximo a vencer, o vencido |
| **Ubicación** | Dirección aproximada y coordenadas del daño, obtenidas por GPS al momento del reporte |
| **Fecha** | Fecha y hora en que se creó el reporte o incidente |
| **Reporte consolidado / incidente** | Agrupación de uno o más reportes ciudadanos que corresponden al mismo daño físico, generada automáticamente por el sistema para evitar duplicados |
| **Confianza del modelo** | Nivel de certeza con el que el modelo de visión computacional clasificó el tipo y severidad del daño en la fotografía |

---

## 8. Preguntas frecuentes

**No puedo iniciar sesión.**
Verificar que el nombre de usuario y la contraseña sean correctos. Si el problema persiste, confirmar que la cuenta esté activa; una cuenta desactivada por un administrador no puede iniciar sesión.

**No aparece mi reporte.**
Si el reporte se creó sin conexión a internet, puede tardar en sincronizarse. Revisar el aviso de reportes pendientes en la aplicación móvil. Si ya se sincronizó y aún no aparece, verificar la conexión e intentar recargar la lista.

**No se carga el mapa.**
Confirmar la conexión a internet. Si el problema continúa, recargar la página o reiniciar la aplicación.

**La fotografía no se envía.**
Verificar que la aplicación tenga permiso de cámara y almacenamiento concedido, y que exista conexión a internet o que el reporte quede guardado como pendiente para sincronización automática.

**¿Cómo sé que mi reporte fue recibido?**
El reporte aparece inmediatamente en la lista de "Mis reportes" con estado "Analizando" o "Pendiente". Ese estado cambia conforme el equipo municipal revisa el reporte.

**¿Puedo editar o eliminar un reporte ya enviado?**
No. Una vez enviado, un reporte no puede modificarse ni eliminarse desde la aplicación móvil ni desde el portal web.

**Olvidé mi contraseña, ¿cómo la recupero?**
Actualmente el sistema no cuenta con un mecanismo de recuperación de contraseña autoservicio. Es necesario solicitar asistencia a un administrador del sistema.

---

## 9. Solución de problemas

| Problema | Posible causa | Solución |
|---|---|---|
| No se puede iniciar sesión | Credenciales incorrectas o cuenta desactivada | Verificar usuario y contraseña; contactar a un administrador si la cuenta fue desactivada |
| El registro no se completa | Las contraseñas ingresadas no coinciden | Verificar que ambos campos de contraseña sean idénticos |
| El reporte queda como "pendiente" mucho tiempo | Sin conexión a internet en el dispositivo | Verificar la conexión; el reporte se enviará automáticamente al recuperar señal |
| No se puede tomar la fotografía | Permiso de cámara no concedido | Revisar los permisos de la aplicación en la configuración del dispositivo |
| No se detecta la ubicación | Permiso de ubicación no concedido o GPS desactivado | Activar el GPS del dispositivo y conceder el permiso de ubicación |
| No aparecen incidentes al filtrar | Filtros demasiado restrictivos | Limpiar los filtros aplicados desde el panel de filtros y volver a intentar |
| No se puede cambiar el estado de un incidente | El usuario no tiene rol Supervisor o Administrador | Iniciar sesión con una cuenta con el rol correspondiente |
| No se puede acceder a Usuarios o Configuración | El rol de la cuenta no tiene permisos suficientes | Configuración requiere rol Administrador; solicitar el cambio de rol a un administrador |

---

## 10. Buenas prácticas

- Tomar la fotografía del daño de la forma más clara posible, con buena iluminación y a una distancia que permita ver el bache o grieta completo.
- Confirmar que la ubicación sugerida por la aplicación corresponda al lugar real del daño antes de enviar el reporte.
- Revisar periódicamente el estado de los reportes enviados desde el historial.
- Para el personal municipal: mantener actualizado el estado de los incidentes conforme avanza su atención, para que el indicador de SLA refleje la situación real.
- Antes de modificar los parámetros de la sección Configuración, entender el efecto que cada peso tiene sobre el cálculo de prioridad.
- Asignar el rol correcto a cada cuenta de personal desde la sección Usuarios, siguiendo el principio de menor privilegio necesario.

---

## 11. Glosario

**Incidente:** agrupación de uno o más reportes que corresponden al mismo daño vial, generada automáticamente por el sistema.

**Reporte:** registro individual creado por un ciudadano al fotografiar un daño vial, con su ubicación y descripción.

**Prioridad:** nivel de atención sugerido para un incidente, calculado a partir de severidad, antigüedad, tipo de daño, ubicación y cantidad de reportes asociados.

**Severidad:** nivel de gravedad del daño detectado (Baja, Media o Alta).

**Visión computacional:** técnica de inteligencia artificial que permite al sistema analizar una fotografía y clasificar automáticamente el tipo y severidad del daño.

**Detección:** proceso mediante el cual el modelo de visión computacional identifica un bache o grieta en una fotografía.

**Consolidación:** proceso mediante el cual el sistema agrupa reportes distintos que corresponden al mismo daño físico, evitando duplicados.

**SLA (Service Level Agreement):** tiempo de respuesta y resolución esperado para la atención de un incidente.

**Administrador:** usuario con permisos completos sobre el sistema, incluida la gestión de usuarios y configuración del algoritmo de prioridad.

**Supervisor:** usuario del personal municipal con permisos para revisar y actualizar el estado de los incidentes.

**Ciudadano:** usuario que reporta daños viales y da seguimiento a sus propios reportes.
