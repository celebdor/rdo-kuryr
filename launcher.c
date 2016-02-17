#include <Python.h>
#include <stdio.h>

int
main(int argc, char *argv[])
{
  Py_SetProgramName(argv[0]);  /* optional but recommended */
  Py_Initialize();
  FILE *script = fopen("/usr/bin/kuryr-server", "r");
  int res = PyRun_SimpleFile(script, "script");
  Py_Finalize();
  return res;
}
