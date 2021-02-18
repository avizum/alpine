from akinator.async_aki import Akinator
import akinator
import asyncio

aki = Akinator()

async def main():
    q = await aki.start_game()

    while aki.progression <= 80:
        a = input(q + "\n\t")
        if a == "b":
            try:
                q = await aki.back()
            except akinator.CantGoBackAnyFurther:
                pass
        else:
            q = await aki.answer(a)
    await aki.win()

    correct = input(f"It's {aki.first_guess['name']} ({aki.first_guess['description']})! Was I correct?\n{aki.first_guess['absolute_picture_path']}\n\t")
    if correct.lower() == "yes" or correct.lower() == "y":
        print("Yay\n")
    else:
        print("Oof\n")

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()