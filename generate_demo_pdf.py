from pathlib import Path

from reportlab.pdfgen import canvas

text = """Operating Systems: Process scheduling is the method used by the operating system to decide which process gets CPU time. A process is a running program that may have multiple threads. The kernel manages resources and scheduling algorithms such as FCFS and Round Robin.

Database Systems: A database stores data in tables and uses SQL queries to access or update records. A primary key uniquely identifies each row and indexes improve query performance.

Machine Learning: In supervised learning, a model learns from labeled data. Regression predicts continuous values while classification predicts categories.

Data Structures: A stack follows the Last In First Out principle, whereas a queue follows the First In First Out principle. Trees and graphs are used to organize hierarchical and networked data."""

output = Path(__file__).resolve().parent / 'demo_data' / 'sample_learning_text.pdf'
output.parent.mkdir(exist_ok=True)

c = canvas.Canvas(str(output))
y = 760
for line in text.splitlines():
    c.drawString(60, y, line[:110])
    y -= 26
c.save()
print(f'Created {output}')
