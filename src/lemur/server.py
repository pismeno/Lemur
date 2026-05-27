from werkzeug.serving import run_simple
from lemur.kernel import application

if __name__ == "__main__":
    print("---------------------------------------------")
    print(" Lemur Server Active!")
    print(" Local address: http://127.0.0.1:8000/")
    print("---------------------------------------------")
    
    run_simple('127.0.0.1', 8000, application, use_reloader=True, use_debugger=True)