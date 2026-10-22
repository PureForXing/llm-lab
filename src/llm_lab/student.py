from pydantic import BaseModel, Field

class Student(BaseModel):
    name: str = Field(..., description="学生姓名")
    age: int = Field(..., description="学生年龄")
    grade: str = Field(..., description="学生年级")
    
    user_name: str = Field(default="", description="用户输入的名字")
    
    def say(self) -> str:
        return f"我的名字叫{self.name}, 我今年 {self.age} 岁了，我在 {self.grade} 年级。"
    
    def answer(self):
        userInput = input("请问你叫什么名字？")
        self.user_name = userInput

    def hello(self) -> str:
        if not self.user_name.strip():
            return "不告诉我名字也没关系，我还是很高兴认识你！"
        return f"你好，很高兴认识你, {self.user_name}!"    
    
stu = Student(name="小明", age=10, grade="五年级")
print(stu.say())
stu.answer()
print(stu.hello())